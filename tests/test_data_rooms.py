from shelter.data.rooms import ROOM_TEMPLATES, BUILDABLE_ROOM_KEYS
from shelter.data.job_types import JOB_DEFINITIONS
from shelter.data.ruins import RUIN_TYPES


REQUIRED_ROOM_FIELDS = {
    "key", "name", "description", "build_cost", "build_time",
    "job_type", "job_slots", "production_per_day", "consumption_per_day",
    "upgrades_to", "downgrade_to",
}


def test_all_rooms_have_required_fields():
    for key, room in ROOM_TEMPLATES.items():
        for field in REQUIRED_ROOM_FIELDS:
            assert field in room, f"{key} missing field: {field}"


def test_all_buildable_rooms_have_non_negative_costs():
    for key in BUILDABLE_ROOM_KEYS:
        room = ROOM_TEMPLATES[key]
        for res, amount in room["build_cost"].items():
            assert amount >= 0, f"{key} has negative cost for {res}"
        assert room["build_time"] >= 0, f"{key} has negative build_time"


def test_all_job_types_referenced_by_rooms_exist():
    for room in ROOM_TEMPLATES.values():
        job_type = room.get("job_type")
        if job_type is not None:
            assert job_type in JOB_DEFINITIONS, f"unknown job_type: {job_type}"


def test_upgrade_chains_are_consistent():
    for key, room in ROOM_TEMPLATES.items():
        for upg_key in room.get("upgrades_to", []):
            assert upg_key in ROOM_TEMPLATES, f"{key} upgrades_to unknown room: {upg_key}"
            upg = ROOM_TEMPLATES[upg_key]
            assert upg.get("downgrade_to") == key, f"{key} -> {upg_key} but downgrade is {upg.get('downgrade_to')}"


def test_ruin_clears_to_valid_room_or_empty():
    for key, ruin in RUIN_TYPES.items():
        clears_to = ruin.get("clears_to")
        if clears_to is not None:
            assert clears_to in ROOM_TEMPLATES, f"{key} clears_to unknown room: {clears_to}"
