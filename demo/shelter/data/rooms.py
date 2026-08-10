"""Shelter — room template definitions.

Each room template defines:
  - job_type: str | None   — which job type this room provides (None = passive room)
  - job_slots: int         — number of job slots (0 = no workers needed)
  - passive_consumption: dict (optional) — per-room resource drain (worker-independent)
  - on_built_effect: str   (optional) — special effect when room is built
"""

ROOM_TEMPLATES = {
    "generator": {
        "key": "generator",
        "name": "发电机房",
        "description": "基础发电设施，为避难所提供稳定电力。",
        "build_cost": {"scrap": 80},
        "build_time": 15,
        "job_type": "power_tech",
        "job_slots": 2,
        "upgrades_to": ["advanced_generator"],
        "downgrade_to": None,
    },
    "water_purifier": {
        "key": "water_purifier",
        "name": "净水房",
        "description": "过滤地下水与回收废水，产出净水。",
        "build_cost": {"scrap": 60},
        "build_time": 12,
        "job_type": "water_tech",
        "job_slots": 2,
        "upgrades_to": ["advanced_purifier"],
        "downgrade_to": None,
    },
    "farm": {
        "key": "farm",
        "name": "种植房",
        "description": "地下温室，利用人工光源种植作物。",
        "build_cost": {"scrap": 50},
        "build_time": 20,
        "job_type": "farmer",
        "job_slots": 3,
        "upgrades_to": ["hydroponics"],
        "downgrade_to": None,
    },
    "warehouse": {
        "key": "warehouse",
        "name": "仓库",
        "description": "存放物资，提升废料存储上限。需电力维持。",
        "build_cost": {"scrap": 40},
        "build_time": 8,
        "job_type": None,
        "job_slots": 0,
        "passive_consumption": {"power": 0.2},
        "upgrades_to": ["large_warehouse"],
        "downgrade_to": None,
        "on_built_effect": "increase_scrap_cap_50",
    },
}

# ---- upgrades ----

ROOM_TEMPLATES["advanced_generator"] = {
    "key": "advanced_generator",
    "name": "高级发电机",
    "description": "高效发电机组，输出功率大幅提升。",
    "build_cost": {"scrap": 150, "power": 50},
    "build_time": 30,
    "job_type": "senior_power_tech",
    "job_slots": 3,
    "upgrades_to": [],
    "downgrade_to": "generator",
}

ROOM_TEMPLATES["advanced_purifier"] = {
    "key": "advanced_purifier",
    "name": "高级净水房",
    "description": "多级过滤系统，净水效率显著提高。",
    "build_cost": {"scrap": 120, "power": 30},
    "build_time": 25,
    "job_type": "senior_water_tech",
    "job_slots": 3,
    "upgrades_to": [],
    "downgrade_to": "water_purifier",
}

ROOM_TEMPLATES["hydroponics"] = {
    "key": "hydroponics",
    "name": "水培农场",
    "description": "全自动水培系统，食物产量大幅提升。",
    "build_cost": {"scrap": 120, "water": 40},
    "build_time": 28,
    "job_type": "hydroponics_tech",
    "job_slots": 3,
    "upgrades_to": [],
    "downgrade_to": "farm",
}

ROOM_TEMPLATES["large_warehouse"] = {
    "key": "large_warehouse",
    "name": "大型仓库",
    "description": "扩容仓储区，大幅提升物资存储上限。需更多电力。",
    "build_cost": {"scrap": 100},
    "build_time": 15,
    "job_type": None,
    "job_slots": 0,
    "passive_consumption": {"power": 0.4},
    "upgrades_to": [],
    "downgrade_to": "warehouse",
    "on_built_effect": "increase_scrap_cap_100",
}


def get_room(key: str) -> dict | None:
    """Look up a room template by key."""
    return ROOM_TEMPLATES.get(key)


def list_buildable() -> list[dict]:
    """Return base rooms that can be built (exclude upgrades)."""
    base_keys = {"generator", "water_purifier", "farm", "warehouse"}
    return [ROOM_TEMPLATES[k] for k in base_keys if k in ROOM_TEMPLATES]
