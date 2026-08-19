"""Tests for systems/resource_system.py."""

import pytest
from shelter.game_state import GameState
from shelter.systems import resource_system
from shelter.systems.room_system import _make_room_slot
from shelter.config import ROOM_STATE_BUILT, DAY_LENGTH_SECONDS


def _built_slot(room_type: str):
    return _make_room_slot(ROOM_STATE_BUILT, room_type=room_type, revealed=True)


def test_tick_produces_power_when_worker_assigned(monkeypatch):
    state = GameState()
    state.population = 3
    state.job_assignment["power_tech"] = 1
    state.floors = [[_built_slot("power_1")]]

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    monkeypatch.setattr(resource_system.time, "time", lambda: DAY_LENGTH_SECONDS)
    resource_system.tick(state)

    assert state.power > 0
    assert state.power <= state.max_power


def test_tick_consumes_water_and_food_per_population(monkeypatch):
    state = GameState()
    state.population = 3
    state.water = 30
    state.food = 30
    state.floors = [[_built_slot("power_1")]]

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    monkeypatch.setattr(resource_system.time, "time", lambda: DAY_LENGTH_SECONDS)
    resource_system.tick(state)

    assert state.water == 27
    assert state.food == 27


def test_infinite_resources_skips_consumption(monkeypatch):
    state = GameState()
    state.infinite_resources = True
    state.population = 3
    state.water = 0
    state.food = 0

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    monkeypatch.setattr(resource_system.time, "time", lambda: DAY_LENGTH_SECONDS * 10)
    msgs = resource_system.tick(state)

    assert state.water == 0
    assert state.food == 0
    assert not any("耗尽" in m for m in msgs)


def test_resources_are_clamped_to_max(monkeypatch):
    state = GameState()
    state.power = 1000
    state.max_power = 50
    state.population = 0
    state.floors = []

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    monkeypatch.setattr(resource_system.time, "time", lambda: DAY_LENGTH_SECONDS)
    resource_system.tick(state)

    assert state.power == 50


def test_tick_with_zero_dt_does_nothing(monkeypatch):
    state = GameState()
    state.water = 20
    state.food = 20

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    msgs = resource_system.tick(state)

    assert state.water == 20
    assert state.food == 20
    assert msgs == []


def test_passive_consumption_applied_without_workers(monkeypatch):
    state = GameState()
    state.population = 0
    state.power = 20
    state.floors = [[_built_slot("water_tank_1")]]

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    monkeypatch.setattr(resource_system.time, "time", lambda: DAY_LENGTH_SECONDS)
    resource_system.tick(state)

    assert state.power < 20


def test_starvation_warning_when_resource_depleted(monkeypatch):
    state = GameState()
    state.population = 10
    state.water = 0
    state.food = 0
    state.floors = []

    monkeypatch.setattr(resource_system.time, "time", lambda: 0.0)
    state.last_resource_tick = 0.0

    # Warning cooldown is 60 seconds, so advance past that.
    monkeypatch.setattr(resource_system.time, "time", lambda: 61.0)
    msgs = resource_system.tick(state)

    assert any("水已耗尽" in m for m in msgs)
    assert any("食物已耗尽" in m for m in msgs)
