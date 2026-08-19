from shelter.game_state import GameState
from shelter.config import TAB_STATUS, INITIAL_POPULATION, INITIAL_WATER, INITIAL_FOOD


def test_default_game_state():
    state = GameState()
    assert state.active_tab == TAB_STATUS
    assert state.population == INITIAL_POPULATION
    assert state.water == INITIAL_WATER
    assert state.food == INITIAL_FOOD
    assert state.scrap == 0
    assert state.story_active
    assert state.story_current_key == "intro"


def test_assign_and_unassign_worker():
    state = GameState()
    state.population = 5
    assert state.assign_worker("power_tech")
    assert state.job_assignment["power_tech"] == 1
    assert state.free_workers == 4

    assert state.unassign_worker("power_tech")
    assert state.job_assignment.get("power_tech", 0) == 0
    assert state.free_workers == 5


def test_assign_worker_respects_slots():
    state = GameState()
    state.population = 5
    # Force an empty floor layout so no job slots exist.
    from shelter.systems.room_system import _make_room_slot
    from shelter.config import ROOM_STATE_EMPTY

    state.floors = [[_make_room_slot(ROOM_STATE_EMPTY, revealed=True)]]
    assert not state.assign_worker("power_tech")


def test_add_and_remove_item():
    state = GameState()
    state.max_items = 5
    added = state.add_item("test_item_a", 3)
    assert added == 3
    assert state.items["test_item_a"] == 3

    removed = state.remove_item("test_item_a", 2)
    assert removed == 2
    assert state.items["test_item_a"] == 1


def test_item_cap():
    state = GameState()
    state.max_items = 2
    added = state.add_item("test_item_a", 5)
    assert added == 2
    assert state.total_item_slots() == 2
