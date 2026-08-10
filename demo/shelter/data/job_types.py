"""Shelter — job type definitions with per-worker production/consumption rates."""

JOB_DEFINITIONS = {
    "power_tech": {
        "key": "power_tech",
        "name": "电力技术员",
        "production": {"power": 0.5},
        "consumption": {},
        "description": "维护基础发电设备",
    },
    "senior_power_tech": {
        "key": "senior_power_tech",
        "name": "高级电力工程师",
        "production": {"power": 1.2},
        "consumption": {},
        "description": "操作高效发电机组",
    },
    "water_tech": {
        "key": "water_tech",
        "name": "净水技术员",
        "production": {"water": 0.3},
        "consumption": {"power": 0.1},
        "description": "操作基础净水设备",
    },
    "senior_water_tech": {
        "key": "senior_water_tech",
        "name": "高级净水工程师",
        "production": {"water": 0.7},
        "consumption": {"power": 0.2},
        "description": "操作多级过滤系统",
    },
    "farmer": {
        "key": "farmer",
        "name": "种植员",
        "production": {"food": 0.2},
        "consumption": {"water": 0.1, "power": 0.05},
        "description": "照料地下温室作物",
    },
    "hydroponics_tech": {
        "key": "hydroponics_tech",
        "name": "水培技术员",
        "production": {"food": 0.6},
        "consumption": {"water": 0.25, "power": 0.15},
        "description": "管理全自动水培系统",
    },
}


def get_job(key: str) -> dict | None:
    """Look up a job type definition by key."""
    return JOB_DEFINITIONS.get(key)
