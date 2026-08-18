"""Shelter — room template definitions.

Each template defines one specific room grade. The key naming convention:
  <function>_<level>   e.g. power_0, power_1, warehouse_1

Fields:
  - job_type: str | None — which job type this room provides
  - job_slots: int — number of workers the room can hold
  - production_per_day: dict — per-worker daily production (only while assigned)
  - consumption_per_day: dict — per-worker daily consumption (only while assigned)
  - passive_consumption_per_day: dict — per-room daily drain regardless of workers
  - cap_effects: dict — changes to resource/item caps when built
  - on_built_effect: str (optional) — legacy special effect hook
"""

ROOM_TEMPLATES = {
    # ============================================================
    # Power
    # ============================================================
    "power_0": {
        "key": "power_0",
        "name": "损坏的发电机",
        "description": "外壳开裂、线路裸露的发电机，只能输出微弱电力。",
        "build_cost": {},
        "build_time": 0,
        "job_type": "power_tech",
        "job_slots": 1,
        "production_per_day": {"power": 3},
        "consumption_per_day": {},
        "upgrades_to": ["power_1"],
        "downgrade_to": None,
        "is_damaged": True,
    },
    "power_1": {
        "key": "power_1",
        "name": "简陋的发电机",
        "description": "重新接好线路的基础发电设备，输出稳定。",
        "build_cost": {"scrap": 15},
        "build_time": 10,
        "job_type": "power_tech",
        "job_slots": 1,
        "production_per_day": {"power": 6},
        "consumption_per_day": {},
        "upgrades_to": [],
        "downgrade_to": "power_0",
    },

    # ============================================================
    # Water
    # ============================================================
    "water_0": {
        "key": "water_0",
        "name": "损坏的滤水器",
        "description": "滤芯堵塞、泵体老化的净水装置，有人值守时才能运转。",
        "build_cost": {},
        "build_time": 0,
        "job_type": "water_tech",
        "job_slots": 1,
        "production_per_day": {"water": 3},
        "consumption_per_day": {"power": 1},
        "upgrades_to": ["water_1"],
        "downgrade_to": None,
        "is_damaged": True,
    },
    "water_1": {
        "key": "water_1",
        "name": "简陋的滤水器",
        "description": "更换滤芯后的基础净水设备，产出足以维持小规模人口。",
        "build_cost": {"scrap": 15},
        "build_time": 10,
        "job_type": "water_tech",
        "job_slots": 1,
        "production_per_day": {"water": 6},
        "consumption_per_day": {"power": 1},
        "upgrades_to": [],
        "downgrade_to": "water_0",
    },

    # ============================================================
    # Food
    # ============================================================
    "food_0": {
        "key": "food_0",
        "name": "损坏的种植槽",
        "description": "灯管频闪、土壤板结的地下种植槽，需要人工维持。",
        "build_cost": {},
        "build_time": 0,
        "job_type": "farmer",
        "job_slots": 1,
        "production_per_day": {"food": 3},
        "consumption_per_day": {"power": 1},
        "upgrades_to": ["food_1"],
        "downgrade_to": None,
        "is_damaged": True,
    },
    "food_1": {
        "key": "food_1",
        "name": "简陋的种植槽",
        "description": "修好补光灯和灌溉系统的基础种植槽。",
        "build_cost": {"scrap": 15},
        "build_time": 10,
        "job_type": "farmer",
        "job_slots": 1,
        "production_per_day": {"food": 6},
        "consumption_per_day": {"power": 1},
        "upgrades_to": [],
        "downgrade_to": "food_0",
    },

    # ============================================================
    # Storage
    # ============================================================
    "warehouse_0": {
        "key": "warehouse_0",
        "name": "半塌的仓库",
        "description": "被碎石掩埋的仓储区，清理后勉强能存放少量物资。",
        "build_cost": {},
        "build_time": 0,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "cap_effects": {"max_scrap": 50, "max_items": 10},
        "upgrades_to": ["warehouse_1"],
        "downgrade_to": None,
        "is_damaged": True,
    },
    "warehouse_1": {
        "key": "warehouse_1",
        "name": "简陋的仓库",
        "description": "加固货架后的仓储区，能存放更多废料和物品。",
        "build_cost": {"scrap": 15},
        "build_time": 10,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "cap_effects": {"max_scrap": 100, "max_items": 30},
        "upgrades_to": [],
        "downgrade_to": "warehouse_0",
    },
    "battery_1": {
        "key": "battery_1",
        "name": "蓄电池组",
        "description": "旧时代储能电池重组，提升电力储备上限。",
        "build_cost": {"scrap": 10},
        "build_time": 10,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "cap_effects": {"max_power": 50},
        "upgrades_to": [],
        "downgrade_to": None,
    },
    "water_tank_1": {
        "key": "water_tank_1",
        "name": "水箱",
        "description": "密封储水罐，可储存更多净水，需要少量电力维持低温。",
        "build_cost": {"scrap": 10},
        "build_time": 10,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "passive_consumption_per_day": {"power": 0.5},
        "cap_effects": {"max_water": 50},
        "upgrades_to": [],
        "downgrade_to": None,
    },
    "food_storage_1": {
        "key": "food_storage_1",
        "name": "冰库",
        "description": "小型冷藏室，延缓食物腐败，需要少量电力维持运转。",
        "build_cost": {"scrap": 10},
        "build_time": 10,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "passive_consumption_per_day": {"power": 0.5},
        "cap_effects": {"max_food": 50},
        "upgrades_to": [],
        "downgrade_to": None,
    },

    # ============================================================
    # Special
    # ============================================================
    "gate": {
        "key": "gate",
        "name": "避难所大门",
        "description": "通往地表的坚固防爆门，是避难所的起点。",
        "build_cost": {},
        "build_time": 0,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "upgrades_to": [],
        "downgrade_to": None,
    },
    "elevator": {
        "key": "elevator",
        "name": "电梯井",
        "description": "连接上下层的垂直通道，维修后可提供跨层视野。",
        "build_cost": {},
        "build_time": 0,
        "job_type": None,
        "job_slots": 0,
        "production_per_day": {},
        "consumption_per_day": {},
        "upgrades_to": [],
        "downgrade_to": None,
    },
}

# Base rooms that can be built directly on empty slots (not upgrades).
# The player must have unlocked the blueprint first.
BUILDABLE_ROOM_KEYS = {
    "power_1",
    "water_1",
    "food_1",
    "warehouse_1",
    "battery_1",
    "water_tank_1",
    "food_storage_1",
}


def get_room(key: str) -> dict | None:
    """Look up a room template by key."""
    return ROOM_TEMPLATES.get(key)


def list_buildable(state=None) -> list[dict]:
    """Return base rooms that can be built on empty slots.

    If `state` is provided, only rooms whose blueprint has been unlocked are returned.
    """
    unlocked = None
    if state is not None:
        unlocked = getattr(state, "unlocked_blueprints", None)
    rooms = []
    for k in BUILDABLE_ROOM_KEYS:
        tmpl = ROOM_TEMPLATES.get(k)
        if not tmpl:
            continue
        if unlocked is not None and k not in unlocked:
            continue
        rooms.append(tmpl)
    return rooms
