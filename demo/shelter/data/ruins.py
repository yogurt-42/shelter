"""Shelter — ruin types with programmable clearance conditions."""

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
    },
    "heavy_rubble": {
        "key": "heavy_rubble",
        "name": "重度废墟",
        "description": "结构坍塌严重，需要大量材料支撑修复。",
        "clear_cost": {"scrap": 80},
        "clear_time": 30,
        "conditions": [],
    },
    "faulty_machinery": {
        "key": "faulty_machinery",
        "name": "故障设备",
        "description": "旧时代的工业机器残骸，体积庞大。",
        "clear_cost": {"scrap": 60, "water": 30},
        "clear_time": 20,
        "conditions": [],
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
# Ruin type assignment for initial floor layout
# ============================================================

# Ruin types assigned per (floor, room) when initializing.
# Only applied to RUIN-state slots; EMPTY slots ignored.
# Keys not listed default to "light_rubble".

INITIAL_RUIN_LAYOUT = {
    # Floor 1 (surface): slots 3-5 are light rubble (default)
    # Floor 2: mixed
    (1, 0): "heavy_rubble",
    (1, 1): "light_rubble",
    (1, 2): "faulty_machinery",
    (1, 3): "light_rubble",
    (1, 4): "heavy_rubble",
    (1, 5): "light_rubble",
    # Floor 3: more severe
    (2, 0): "faulty_machinery",
    (2, 1): "sealed_door",
    (2, 2): "heavy_rubble",
    (2, 3): "faulty_machinery",
    (2, 4): "heavy_rubble",
    (2, 5): "sealed_door",
    # Floor 4: hazardous
    (3, 0): "heavy_rubble",
    (3, 1): "biohazard",
    (3, 2): "sealed_door",
    (3, 3): "heavy_rubble",
    (3, 4): "biohazard",
    (3, 5): "faulty_machinery",
    # Floor 5: deepest — worst
    (4, 0): "biohazard",
    (4, 1): "sealed_door",
    (4, 2): "biohazard",
    (4, 3): "heavy_rubble",
    (4, 4): "biohazard",
    (4, 5): "sealed_door",
}


def get_ruin_for_slot(floor: int, room: int) -> str:
    """Return the ruin type key for a given slot position."""
    return INITIAL_RUIN_LAYOUT.get((floor, room), "light_rubble")
