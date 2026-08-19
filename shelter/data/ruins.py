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
    "warehouse_ruin": {
        "key": "warehouse_ruin",
        "name": "掩埋的仓库",
        "description": "碎石和旧货架掩埋了这片仓储区，清理后可以恢复部分存储功能。",
        "clear_cost": {},
        "clear_time": 10,
        "conditions": [
            {"type": "min_population", "value": 3},
        ],
        "rewards": [],
        "clears_to": "warehouse_0",
        "triggers_event": "starting_funds",
    },
    "debris_front": {
        "key": "debris_front",
        "name": "坍塌残骸",
        "description": "结构坍塌留下的碎石堆，清理后可以作为建造空间。",
        "clear_cost": {},
        "clear_time": 15,
        "conditions": [
            {"type": "min_population", "value": 3},
        ],
        "rewards": [],
        "clears_to": None,
    },
    "debris_back": {
        "key": "debris_back",
        "name": "坍塌残骸",
        "description": "结构坍塌留下的碎石堆，清理后可以作为建造空间。",
        "clear_cost": {},
        "clear_time": 20,
        "conditions": [
            {"type": "min_population", "value": 3},
        ],
        "rewards": [],
        "clears_to": None,
    },
    "elevator_ruin": {
        "key": "elevator_ruin",
        "name": "损坏的电梯井",
        "description": "坍塌的电梯井，需要一次性电力驱动清理设备，清理后可恢复垂直通行。",
        "clear_cost": {"power": 5},
        "clear_time": 20,
        "conditions": [
            {"type": "min_population", "value": 3},
        ],
        "rewards": [],
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
            slot["state"] == ROOM_STATE_BUILT and slot["room_type"] == room_type
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

    elif ctype == "min_population":
        if state.population < condition.get("value", 0):
            return (False, f"need population >= {condition['value']}")
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
    # Floor 1 (surface / upper underground)
    0: [
        {"state": ROOM_STATE_BUILT, "room_type": "gate", "revealed": True},          # R1 避难所大门
        {"state": ROOM_STATE_BUILT, "room_type": "power_0", "revealed": True},       # R2 损坏的发电机
        {"state": ROOM_STATE_BUILT, "room_type": "food_0", "revealed": True},        # R3 损坏的种植槽
        {"state": ROOM_STATE_BUILT, "room_type": "water_0", "revealed": True},       # R4 损坏的滤水器
        {"state": ROOM_STATE_RUIN, "ruin_type": "warehouse_ruin", "revealed": True}, # R5 掩埋的仓库
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_front", "revealed": False},  # R6 坍塌残骸
        {"state": ROOM_STATE_RUIN, "ruin_type": "elevator_ruin", "revealed": False}, # R7 损坏的电梯井
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},   # R8 坍塌残骸
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},   # R9 坍塌残骸
        None,                                                                            # R10 void
    ],
    # Floor 2 (hidden until elevator connects)
    1: [
        None,  # R1 void
        None,  # R2 void
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R3
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R4
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R5
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R6
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R7
        {"state": ROOM_STATE_RUIN, "ruin_type": "elevator_ruin", "revealed": False},  # R8 电梯废墟
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R9
        {"state": ROOM_STATE_RUIN, "ruin_type": "debris_back", "revealed": False},    # R10
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
