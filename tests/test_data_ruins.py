"""Contract tests for data/ruins.py."""

from shelter.data.ruins import RUIN_TYPES, INITIAL_FLOOR_LAYOUT
from shelter.data.rooms import ROOM_TEMPLATES
from shelter.config import ROOMS_PER_FLOOR


REQUIRED_RUIN_FIELDS = {
    "key",
    "name",
    "description",
    "clear_cost",
    "clear_time",
    "conditions",
    "rewards",
    "clears_to",
}


def test_all_ruins_have_required_fields():
    for key, ruin in RUIN_TYPES.items():
        for field in REQUIRED_RUIN_FIELDS:
            assert field in ruin, f"{key} missing field: {field}"


def test_all_ruin_conditions_have_known_types():
    known_types = {"has_resources", "has_room", "stat_check", "min_population"}
    for key, ruin in RUIN_TYPES.items():
        for cond in ruin.get("conditions", []):
            assert cond.get("type", "") in known_types, f"{key} unknown condition type: {cond}"


def test_ruin_clears_to_valid_room_or_none():
    for key, ruin in RUIN_TYPES.items():
        clears_to = ruin.get("clears_to")
        if clears_to is not None:
            assert clears_to in ROOM_TEMPLATES, f"{key} clears_to unknown room: {clears_to}"


def test_initial_floor_layout_has_required_floors():
    # The game expects at least floors 0..FLOORS-1; floors may be empty if not designed.
    from shelter.config import FLOORS

    for floor in range(FLOORS):
        assert floor in INITIAL_FLOOR_LAYOUT, f"floor {floor} missing from INITIAL_FLOOR_LAYOUT"


def test_initial_floor_rows_match_room_count():
    for floor, row in INITIAL_FLOOR_LAYOUT.items():
        if row:
            assert len(row) == ROOMS_PER_FLOOR, f"floor {floor} has {len(row)} rooms, expected {ROOMS_PER_FLOOR}"


def test_initial_floor_ruin_types_are_known():
    for floor, row in INITIAL_FLOOR_LAYOUT.items():
        for spec in row or []:
            if spec is None:
                continue
            if spec.get("state") == 1:  # ROOM_STATE_RUIN
                ruin_type = spec.get("ruin_type")
                assert ruin_type in RUIN_TYPES, f"floor {floor} unknown ruin_type: {ruin_type}"


def test_initial_floor_built_rooms_are_known():
    for floor, row in INITIAL_FLOOR_LAYOUT.items():
        for spec in row or []:
            if spec is None:
                continue
            if spec.get("state") == 2:  # ROOM_STATE_BUILT
                room_type = spec.get("room_type")
                assert room_type in ROOM_TEMPLATES, f"floor {floor} unknown room_type: {room_type}"
