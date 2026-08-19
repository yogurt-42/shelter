"""Shelter — room system: all room lifecycle operations.

This module is the single place that mutates room-related state:
  - floor initialization and vision propagation
  - capacity recalculation
  - build / clear / complete construction
  - upgrade / repair / downgrade / demolish
  - resource checks and deductions for room actions

UI code should call functions here instead of modifying `state.floors`
or `state.*` resource caps directly.
"""

import time
from shelter.config import (
    FLOORS,
    ROOMS_PER_FLOOR,
    ROOM_STATE_EMPTY,
    ROOM_STATE_RUIN,
    ROOM_STATE_BUILT,
    ROOM_STATE_BUILDING,
    ROOM_STATE_CLEARING,
    INITIAL_MAX_POWER,
    INITIAL_MAX_WATER,
    INITIAL_MAX_FOOD,
    INITIAL_MAX_SCRAP,
    INITIAL_MAX_ITEMS,
)
from shelter.data.rooms import get_room
from shelter.data.ruins import RUIN_TYPES, get_cell_spec
from shelter.data.items import get_item


# ============================================================
# Floor initialization
# ============================================================

def _make_room_slot(
    state: int,
    ruin_type: str | None = None,
    room_type: str | None = None,
    revealed: bool = False,
    void: bool = False,
    level: int = 1,
) -> dict:
    return {
        "state": state,
        "room_type": room_type,
        "level": level,
        "ruin_type": ruin_type,
        "assigned_workers": 0,
        "build_end_time": None,
        "action_type": None,
        "revealed": revealed,
        "void": void,
    }


def init_floors(state):
    """Initialize floors from the designer-defined layout table."""
    state.floors = []
    for f in range(FLOORS):
        row = []
        for r in range(ROOMS_PER_FLOOR):
            spec = get_cell_spec(f, r)
            if spec is None:
                slot = _make_room_slot(ROOM_STATE_EMPTY, void=True, revealed=False)
            elif spec["state"] == ROOM_STATE_BUILT:
                rt = spec.get("room_type")
                level = 0 if rt and rt.endswith("_0") else 1
                slot = _make_room_slot(
                    ROOM_STATE_BUILT,
                    room_type=rt,
                    revealed=spec.get("revealed", True),
                    level=level,
                )
            elif spec["state"] == ROOM_STATE_EMPTY:
                slot = _make_room_slot(ROOM_STATE_EMPTY, revealed=spec.get("revealed", False))
            else:  # RUIN
                slot = _make_room_slot(
                    ROOM_STATE_RUIN,
                    ruin_type=spec.get("ruin_type", "debris_back"),
                    revealed=spec.get("revealed", False),
                )
            row.append(slot)
        state.floors.append(row)

    propagate_vision(state)


# ============================================================
# Vision
# ============================================================

def propagate_vision(state):
    """Reveal all neighbors reachable from currently revealed rooms."""
    changed = True
    while changed:
        changed = False
        for f in range(len(state.floors)):
            row = state.floors[f]
            for r in range(len(row)):
                slot = row[r]
                if not slot.get("revealed") or slot.get("void"):
                    continue
                if reveal_around(state, f, r):
                    changed = True


def reveal_around(state, floor: int, room: int) -> bool:
    """Reveal neighbors of the given slot according to vision rules.
    Returns True if any new slot was revealed.
    """
    slot = state.floors[floor][room]
    if slot.get("void") or not slot.get("revealed"):
        return False

    changed = False
    room_state = slot["state"]
    room_type = slot.get("room_type")
    is_elevator = room_type == "elevator"
    provides_horizontal = room_state in (ROOM_STATE_EMPTY, ROOM_STATE_BUILT)

    # Horizontal vision: empty / built rooms reveal left/right neighbors.
    if provides_horizontal:
        for dr in (-1, 1):
            nr = room + dr
            if 0 <= nr < len(state.floors[floor]):
                neighbor = state.floors[floor][nr]
                if not neighbor.get("void") and not neighbor.get("revealed"):
                    neighbor["revealed"] = True
                    changed = True

    # Vertical vision: only elevators reveal elevator rooms above/below.
    if is_elevator:
        for df in (-1, 1):
            nf = floor + df
            if 0 <= nf < len(state.floors):
                neighbor = state.floors[nf][room]
                is_elevator_neighbor = (
                    neighbor.get("room_type") == "elevator"
                    or (
                        neighbor.get("state") == ROOM_STATE_RUIN
                        and neighbor.get("ruin_type") == "elevator_ruin"
                    )
                )
                if (
                    not neighbor.get("void")
                    and not neighbor.get("revealed")
                    and is_elevator_neighbor
                ):
                    neighbor["revealed"] = True
                    changed = True

    return changed


def refresh_vision(state):
    """Recalculate vision from all currently revealed rooms."""
    propagate_vision(state)


# ============================================================
# Capacity recalculation
# ============================================================

def recalc_caps(state):
    """Recalculate max resource caps from base values + built room effects."""
    state.max_power = INITIAL_MAX_POWER
    state.max_water = INITIAL_MAX_WATER
    state.max_food = INITIAL_MAX_FOOD
    state.max_scrap = INITIAL_MAX_SCRAP
    state.max_items = INITIAL_MAX_ITEMS

    for floor in state.floors:
        for slot in floor:
            if slot["state"] != ROOM_STATE_BUILT:
                continue
            tmpl = get_room(slot.get("room_type", ""))
            if not tmpl:
                continue
            for key, delta in tmpl.get("cap_effects", {}).items():
                if key == "max_power":
                    state.max_power += delta
                elif key == "max_water":
                    state.max_water += delta
                elif key == "max_food":
                    state.max_food += delta
                elif key == "max_scrap":
                    state.max_scrap += delta
                elif key == "max_items":
                    state.max_items += delta


# ============================================================
# Room lifecycle
# ============================================================

def start_building(state, floor: int, room: int, room_key: str, build_time: float):
    slot = get_room_slot(state, floor, room)
    slot["state"] = ROOM_STATE_BUILDING
    slot["room_type"] = room_key
    slot["revealed"] = True
    if state.full_speed:
        build_time = 0
    slot["build_end_time"] = time.time() + build_time
    slot["action_type"] = "building"


def start_clearing(state, floor: int, room: int, clear_time: float):
    slot = get_room_slot(state, floor, room)
    slot["state"] = ROOM_STATE_CLEARING
    slot["revealed"] = True
    if state.full_speed:
        clear_time = 0
    slot["build_end_time"] = time.time() + clear_time
    slot["action_type"] = "clearing"


def complete_construction(state, floor: int, room: int):
    """Called when a build/clear timer finishes."""
    slot = get_room_slot(state, floor, room)
    slot["revealed"] = True
    action = slot["action_type"]
    if action == "building":
        slot["state"] = ROOM_STATE_BUILT
        slot["level"] = 1
        slot["assigned_workers"] = 0
        _apply_build_effect(state, slot.get("room_type"))
    elif action == "clearing":
        ruin_type = slot.get("ruin_type")
        slot["ruin_type"] = None
        _award_ruin_rewards(state, ruin_type)
        ruin_data = RUIN_TYPES.get(ruin_type, {})
        clears_to = ruin_data.get("clears_to")
        if clears_to:
            slot["state"] = ROOM_STATE_BUILT
            slot["room_type"] = clears_to
            slot["level"] = 0 if clears_to.endswith("_0") else 1
            slot["assigned_workers"] = 0
            _apply_build_effect(state, clears_to)
        else:
            slot["state"] = ROOM_STATE_EMPTY

        # Trigger one-time ruin events (e.g. starting funds).
        event_key = ruin_data.get("triggers_event")
        if event_key:
            _trigger_event(state, event_key)

    slot["build_end_time"] = None
    slot["action_type"] = None
    # Vision may have expanded: re-run propagation.
    refresh_vision(state)


def _apply_build_effect(state, room_type: str | None):
    """Apply one-time effects when a room finishes construction."""
    if not room_type:
        return

    tmpl = get_room(room_type)
    if not tmpl:
        return

    # Recalculate caps for cap_effects.
    recalc_caps(state)

    # Legacy on_built_effect hook.
    effect = tmpl.get("on_built_effect")
    if effect == "increase_scrap_cap_50":
        state.max_scrap += 50
        state.add_log(f"仓库扩容：废料上限 +50（当前 {int(state.max_scrap)}）")
    elif effect == "increase_scrap_cap_100":
        state.max_scrap += 100
        state.add_log(f"大型仓库扩容：废料上限 +100（当前 {int(state.max_scrap)}）")


def _trigger_event(state, event_key: str):
    """Handle one-time ruin-triggered events."""
    if event_key == "starting_funds":
        state.power += 5
        state.water += 10
        state.food += 10
        state.scrap += 40
        state.unlock_blueprint(
            "power_1", "water_1", "food_1",
            "warehouse_1", "battery_1", "water_tank_1", "food_storage_1",
        )
        state.add_log("在废墟中发现了旧世界储备。获得启动资金，解锁 1 级建筑图纸。")


def _award_ruin_rewards(state, ruin_type: str | None):
    """Award items when a ruin is cleared."""
    if not ruin_type:
        return

    ruin_data = RUIN_TYPES.get(ruin_type)
    if not ruin_data:
        return
    for reward in ruin_data.get("rewards", []):
        item_key = reward.get("item")
        count = reward.get("count", 1)
        if not item_key or get_item(item_key) is None:
            continue
        added = state.add_item(item_key, count)
        if added > 0:
            item_name = get_item(item_key)["name"]
            state.add_log(f"清理废墟获得：{item_name} x{added}")
        if added < count:
            state.add_log("物品栏已满，部分奖励已丢失。")


# ============================================================
# Room actions (upgrade / repair / downgrade / demolish)
# ============================================================

def get_room_slot(state, floor: int, room: int) -> dict:
    return state.floors[floor][room]


def can_demolish(state, floor: int, room: int) -> bool:
    slot = get_room_slot(state, floor, room)
    return slot["state"] == ROOM_STATE_BUILT


def demolish_room(state, floor: int, room: int):
    """Demolish a built room, returning it to empty."""
    slot = get_room_slot(state, floor, room)
    if slot["state"] != ROOM_STATE_BUILT:
        return
    tmpl = get_room(slot.get("room_type", ""))
    old_name = tmpl["name"] if tmpl else "房间"

    slot["state"] = ROOM_STATE_EMPTY
    slot["room_type"] = None
    slot["level"] = 1
    slot["assigned_workers"] = 0
    state.add_log(f"{old_name} 已拆除。")
    recalc_caps(state)
    refresh_vision(state)


def get_upgrade_options(state, floor: int, room: int) -> list[dict]:
    """Return available upgrade/repair options for a built room.
    Each option is a dict:
        action_type: "upgrade" | "repair" | "downgrade"
        target_key: str
        target_tmpl: dict | None
        cost: dict
        label: str
        subtext: str
    """
    slot = get_room_slot(state, floor, room)
    tmpl = get_room(slot.get("room_type", ""))
    if not tmpl:
        return []

    actions = []
    for uk in tmpl.get("upgrades_to", []):
        ut = get_room(uk)
        if ut:
            is_repair = tmpl.get("is_damaged", False)
            cost = dict(ut["build_cost"])
            if is_repair:
                cost = {k: max(1, v // 2) for k, v in cost.items()}
            label = "维修" if is_repair else "升级"
            actions.append({
                "action_type": "repair" if is_repair else "upgrade",
                "target_key": uk,
                "target_tmpl": ut,
                "cost": cost,
                "label": f"{label} -> {ut['name']}",
                "subtext": f"费用: {cost_cn(cost)}",
            })

    if tmpl.get("downgrade_to"):
        dt = get_room(tmpl["downgrade_to"])
        if dt:
            actions.append({
                "action_type": "downgrade",
                "target_key": tmpl["downgrade_to"],
                "target_tmpl": dt,
                "cost": {},
                "label": f"降级 -> {dt['name']}",
                "subtext": "无消耗",
            })

    actions.append({
        "action_type": "demolish",
        "target_key": None,
        "target_tmpl": None,
        "cost": {},
        "label": "拆除",
        "subtext": "移除房间，无返还",
    })
    return actions


def apply_room_action(state, floor: int, room: int, action_type: str, target_key: str | None) -> bool:
    """Apply an upgrade/repair/downgrade/demolish action.
    Returns True on success.
    """
    slot = get_room_slot(state, floor, room)
    tmpl = get_room(slot.get("room_type", ""))
    if not tmpl:
        return False

    if action_type == "demolish":
        demolish_room(state, floor, room)
        return True

    if action_type in ("upgrade", "repair"):
        ut = get_room(target_key) if target_key else None
        if not ut:
            return False
        is_repair = tmpl.get("is_damaged", False)
        cost = dict(ut["build_cost"])
        if is_repair:
            cost = {k: max(1, v // 2) for k, v in cost.items()}
        can, failures = check_resources(state, cost)
        if not can:
            for msg in failures:
                state.add_log(msg)
            return False
        deduct_resources(state, cost)
        slot["room_type"] = target_key
        slot["level"] = 0 if target_key.endswith("_0") else 1
        verb = "维修" if is_repair else "升级"
        state.add_log(f"{tmpl['name']} 已{verb}为 {ut['name']}！")
        recalc_caps(state)
        return True

    if action_type == "downgrade":
        dt = get_room(target_key) if target_key else None
        if not dt:
            return False
        slot["room_type"] = target_key
        slot["level"] = 0 if target_key.endswith("_0") else 1
        state.add_log(f"{tmpl['name']} 已降级为 {dt['name']}。")
        recalc_caps(state)
        return True

    return False


# ============================================================
# Resource helpers for room actions
# ============================================================

def check_resources(state, cost: dict) -> tuple[bool, list[str]]:
    """Check if state has enough resources for a cost dict.
    Returns (can_afford: bool, list_of_failure_messages: list[str]).
    """
    if getattr(state, "infinite_resources", False):
        return (True, [])
    failures = []
    for res_key, amount in cost.items():
        current = get_resource(state, res_key)
        if current < amount:
            cn = _res_cn(res_key)
            failures.append(f"{cn}不足：需要 {amount}，当前 {int(current)}")
    return (len(failures) == 0, failures)


def deduct_resources(state, cost: dict):
    """Deduct resources for a cost dict."""
    if getattr(state, "infinite_resources", False):
        return
    for res_key, amount in cost.items():
        attr = _resource_attr(res_key)
        if attr:
            current = getattr(state, attr)
            setattr(state, attr, max(0, current - amount))


def get_resource(state, key: str) -> float:
    attr = _resource_attr(key)
    return getattr(state, attr, 0.0) if attr else 0.0


def set_resource(state, key: str, value: float):
    attr = _resource_attr(key)
    if attr:
        setattr(state, attr, value)


def _resource_attr(key: str) -> str | None:
    return {"power": "power", "water": "water", "food": "food", "scrap": "scrap"}.get(key)


def res_cn(key: str) -> str:
    """Map resource key to Chinese display name."""
    mapping = {"power": "电力", "water": "水", "food": "食物", "scrap": "废料"}
    return mapping.get(key, key)


def cost_cn(cost: dict) -> str:
    """Format a cost dict as Chinese string, e.g. '废料:80  电力:50'."""
    return "  ".join(f"{res_cn(k)}:{v}" for k, v in cost.items())
