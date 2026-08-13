"""Shelter — ruin types with programmable clearance conditions."""

from shelter.config import (
    ROOM_STATE_EMPTY,
    ROOM_STATE_RUIN,
    ROOM_STATE_BUILT,
)

# ============================================================
# Ruin type definitions
# ============================================================

RUIN_TYPES = {
    "light_rubble": {
        "key": "light_rubble",
        "name": "轻度废墟",
        "description": "碎石和废弃物堆积，清理难度较低。",
        "clear_cost": {"scrap": 30},
        "clear_time": 10,
        "conditions": [],
        "rewards": [{"item": "test_item_a", "count": 1}],
    },
    "heavy_rubble": {
        "key": "heavy_rubble",
        "name": "重度废墟",
        "description": "结构坍塌严重，需要大量材料支撑修复。",
        "clear_cost": {"scrap": 80},
        "clear_time": 30,
        "conditions": [],
        "rewards": [{"item": "test_item_a", "count": 2}],
    },
    "faulty_machinery": {
        "key": "faulty_machinery",
        "name": "故障设备",
        "description": "旧时代的工业机器残骸，体积庞大。",
        "clear_cost": {"scrap": 60, "water": 30},
        "clear_time": 20,
        "conditions": [],
        "rewards": [{"item": "test_item_b", "count": 1}],
    },
    "sealed_door": {
        "key": "sealed_door",
        "name": "密封安全门",
        "description": "厚重的防爆门，似乎通向更深的区域。需要足够电力驱动开启装置。",
        "clear_cost": {"scrap": 40},
        "clear_time": 25,
        "conditions": [
            {"type": "stat_check", "min_total_power": 50},
        ],
        "rewards": [{"item": "test_item_a", "count": 1}, {"item": "test_item_b", "count": 1}],
    },
    "biohazard": {
        "key": "biohazard",
        "name": "生物危害区",
        "description": "残留的生化污染物覆盖了整个房间。必须配备净水设备才能安全处理。",
        "clear_cost": {"scrap": 100, "water": 50},
        "clear_time": 45,
        "conditions": [
            {"type": "has_room", "room_type": "water_purifier"},
        ],
        "rewards": [{"item": "test_item_b", "count": 2}],
    },
    "elevator_ruin": {
        "key": "elevator_ruin",
        "name": "损坏的电梯井",
        "description": "坍塌的电梯井，清理后可以恢复垂直通行。",
        "clear_cost": {"scrap": 100, "power": 50},
        "clear_time": 30,
        "conditions": [],
        "rewards": [{"item": "test_item_a", "count": 1}],
        "clears_to": "elevator",
    },
}


# ============================================================
# Condition evaluation
# ============================================================

def evaluate_condition(state, condition: dict) -> tuple[bool, str]:
    """Evaluate a single clearance condition.
    Returns (passed, failure_reason).
    """
    ctype = condition.get("type", "")

    if ctype == "has_resources":
        for res_key, amount in condition.items():
            if res_key == "type":
                continue
            current = _get_resource(state, res_key)
            if current < amount:
                return (False, f"need {amount} {res_key} (have {int(current)})")
        return (True, "")

    elif ctype == "has_room":
        room_type = condition.get("room_type", "")
        found = any(
            slot["state"] == 2 and slot["room_type"] == room_type
            for floor in state.floors
            for slot in floor
        )
        if not found:
            from shelter.data.rooms import get_room
            tmpl = get_room(room_type)
            name = tmpl["name"] if tmpl else room_type
            return (False, f"need built: {name}")
        return (True, "")

    elif ctype == "stat_check":
        if "min_total_power" in condition:
            if state.power < condition["min_total_power"]:
                return (False, f"need total power >= {condition['min_total_power']}")
        if "min_total_water" in condition:
            if state.water < condition["min_total_water"]:
                return (False, f"need total water >= {condition['min_total_water']}")
        # extensible: add more stat checks here
        return (True, "")

    else:
        return (True, "")  # unknown condition type, pass by default


def can_clear(state, ruin_data: dict) -> tuple[bool, list[str]]:
    """Check all conditions for a ruin.
    Returns (can_clear, list_of_failure_reasons).
    """
    reasons = []
    for cond in ruin_data.get("conditions", []):
        passed, reason = evaluate_condition(state, cond)
        if not passed:
            reasons.append(reason)
    return (len(reasons) == 0, reasons)


def _get_resource(state, key: str) -> float:
    """Map resource key to current state value."""
    mapping = {
        "power": state.power,
        "water": state.water,
        "food": state.food,
        "scrap": state.scrap,
    }
    return mapping.get(key, 0.0)


# ============================================================
# Initial floor layout
# ============================================================

# Each floor is a list of cell specs. Length must match ROOMS_PER_FLOOR.
# A cell spec is either:
#   None                        — void (no room, no rendering, no interaction)
#   {"state": ROOM_STATE_BUILT, "room_type": str, "revealed": bool}
#   {"state": ROOM_STATE_EMPTY, "revealed": bool}
#   {"state": ROOM_STATE_RUIN,  "ruin_type": str, "revealed": bool}

INITIAL_FLOOR_LAYOUT = {
    # Floor 1 (surface): only the gate starts revealed; everything else is discovered by the player.
    0: [
        None,  # R1  void
        {"state": ROOM_STATE_BUILT, "room_type": "gate", "revealed": True},  # R2 避难所大门
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R3
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R4
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R5
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R6
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R7
        {"state": ROOM_STATE_RUIN, "ruin_type": "elevator_ruin", "revealed": False},  # R8 电梯废墟
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R9
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R10
    ],
    # Floor 2 (hidden until elevator connects)
    1: [
        None,  # R1 void
        None,  # R2 void
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R3
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R4
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R5
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R6
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R7
        {"state": ROOM_STATE_RUIN, "ruin_type": "elevator_ruin", "revealed": False},  # R8 电梯废墟
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R9
        {"state": ROOM_STATE_RUIN, "ruin_type": "light_rubble", "revealed": False},   # R10
    ],
    # Floors 3-4: not yet designed
    2: [],
    3: [],
}


def get_cell_spec(floor: int, room: int) -> dict | None:
    """Return the initial cell spec for a given slot, or None for void."""
    floor_spec = INITIAL_FLOOR_LAYOUT.get(floor)
    if not floor_spec:
        return None
    if room < 0 or room >= len(floor_spec):
        return None
    return floor_spec[room]
