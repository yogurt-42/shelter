import pytest
from shelter.game_state import GameState
from shelter.systems import room_system
from shelter.config import (
    ROOM_STATE_EMPTY,
    ROOM_STATE_RUIN,
    ROOM_STATE_BUILT,
    ROOM_STATE_BUILDING,
    ROOM_STATE_CLEARING,
)


def _slot(state, room_type="power_1"):
    return room_system._make_room_slot(ROOM_STATE_EMPTY, room_type=room_type, revealed=True)


def test_build_then_complete_sets_room_built(monkeypatch):
    state = GameState()
    state.scrap = 1000
    state.max_scrap = 1000
    state.floors = [[_slot(state, None)]]
    state.unlocked_blueprints.add("power_1")

    slot = state.floors[0][0]
    room_system.start_building(state, 0, 0, "power_1", 10.0)

    assert slot["state"] == ROOM_STATE_BUILDING
    assert slot["room_type"] == "power_1"

    monkeypatch.setattr(room_system.time, "time", lambda: slot["build_end_time"] + 1)
    room_system.complete_construction(state, 0, 0)

    assert slot["state"] == ROOM_STATE_BUILT
    assert slot["level"] == 1


def test_clear_ruin_reveals_empty_slot(monkeypatch):
    state = GameState()
    state.population = 3
    state.floors = [[room_system._make_room_slot(ROOM_STATE_RUIN, ruin_type="debris_front", revealed=True)]]

    slot = state.floors[0][0]
    room_system.start_clearing(state, 0, 0, 0.0)

    assert slot["state"] == ROOM_STATE_CLEARING

    monkeypatch.setattr(room_system.time, "time", lambda: slot["build_end_time"] + 1)
    room_system.complete_construction(state, 0, 0)

    assert slot["state"] == ROOM_STATE_EMPTY


def test_clear_elevator_ruin_becomes_elevator(monkeypatch):
    state = GameState()
    state.population = 3
    state.power = 10
    state.floors = [[room_system._make_room_slot(ROOM_STATE_RUIN, ruin_type="elevator_ruin", revealed=True)]]

    slot = state.floors[0][0]
    room_system.start_clearing(state, 0, 0, 0.0)
    monkeypatch.setattr(room_system.time, "time", lambda: slot["build_end_time"] + 1)
    room_system.complete_construction(state, 0, 0)

    assert slot["state"] == ROOM_STATE_BUILT
    assert slot["room_type"] == "elevator"


def test_repair_damaged_room_half_cost():
    state = GameState()
    state.scrap = 10
    state.max_scrap = 100
    state.unlocked_blueprints.add("power_1")
    state.floors = [[room_system._make_room_slot(ROOM_STATE_BUILT, room_type="power_0", revealed=True)]]

    options = room_system.get_upgrade_options(state, 0, 0)
    repair = next(a for a in options if a["action_type"] == "repair")
    assert repair["cost"]["scrap"] == 7  # half of 15, floor division

    assert room_system.apply_room_action(state, 0, 0, repair["action_type"], repair["target_key"])
    assert state.floors[0][0]["room_type"] == "power_1"
    assert state.scrap == 3


def test_vision_propagates_horizontally():
    state = GameState()
    state.floors = [
        [
            room_system._make_room_slot(ROOM_STATE_BUILT, room_type="gate", revealed=True),
            room_system._make_room_slot(ROOM_STATE_EMPTY, revealed=False),
            room_system._make_room_slot(ROOM_STATE_RUIN, ruin_type="debris_front", revealed=False),
        ]
    ]
    room_system.propagate_vision(state)
    assert state.floors[0][1]["revealed"]
    assert state.floors[0][2]["revealed"]
