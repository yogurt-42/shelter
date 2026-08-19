"""Tests for systems/story_system.py.

Note on "condition" event semantics: the current implementation sets
``story_event_index = target`` inside the condition handler, but the caller
still increments the index by one afterwards. Therefore ``then``/``else``
targets effectively point one event *before* the desired next event. The
tests below reflect this actual behaviour.
"""

import time

from shelter.game_state import GameState
from shelter.systems import story_system
from shelter.config import TAB_STATUS, TAB_BUILD, TAB_POPULATION, TAB_MATERIALS


def _reset_story(state, events, key="test"):
    """Replace the active story with a controlled event list."""
    state.story_events = list(events)
    state.story_event_index = 0
    state.story_paused = False
    state.story_active = True
    state.story_current_key = key
    state.story_last_event_time = time.time()
    state.story_popup_title = ""
    state.story_popup_text = ""
    state.story_popup_mode = "info"
    state.story_choices = None
    state.story_queue = []


def test_log_event_adds_line():
    state = GameState()
    _reset_story(state, [(0.0, "log", "hello story", False)])

    story_system.tick(state)

    assert "hello story" in state.logs
    assert state.story_event_index == 1


def test_unlock_tab_reveals_tab_and_pauses():
    state = GameState()
    # Add a trailing non-blocking event so the story is not finished
    # immediately while the blocking popup is open.
    _reset_story(state, [
        (0.0, "unlock_tab", {
            "tab": TAB_BUILD,
            "title": "建筑",
            "text": "建筑标签说明",
            "log": "建筑已解锁",
        }, True),
        (0.0, "log", "after unlock", False),
    ])

    story_system.tick(state)

    assert TAB_BUILD in state.visible_tabs
    assert state.story_paused
    assert state.story_pause_tab == TAB_BUILD
    assert state.story_resume_tab == TAB_STATUS
    assert state.story_popup_mode == "info"
    assert "建筑已解锁" in state.logs
    assert state.story_event_index == 1


def test_resume_story_clears_pause_state():
    state = GameState()
    _reset_story(state, [(0.0, "log", "done", False)])
    state.story_paused = True
    state.story_pause_tab = TAB_BUILD
    state.story_resume_tab = TAB_STATUS

    story_system.resume_story(state)

    assert not state.story_paused
    assert state.story_pause_tab is None
    assert state.story_resume_tab is None


def test_unlock_blueprint_unlocks_keys_and_logs():
    state = GameState()
    _reset_story(state, [
        (0.0, "unlock_blueprint", {"keys": ["power_1", "water_1"], "log": "蓝图已解锁"}, False),
    ])

    story_system.tick(state)

    assert "power_1" in state.unlocked_blueprints
    assert "water_1" in state.unlocked_blueprints
    assert "蓝图已解锁" in state.logs


def test_flag_sets_story_flags():
    state = GameState()
    _reset_story(state, [
        (0.0, "flag", {"set": {"welcomed": True, "door_open": False}}, False),
    ])

    story_system.tick(state)

    assert state.story_flags["welcomed"] is True
    assert state.story_flags["door_open"] is False


def test_choice_pauses_and_jump_works():
    state = GameState()
    _reset_story(state, [
        (0.0, "choice", {
            "title": "选择",
            "text": "A 还是 B",
            "choices": [
                {"text": "A", "jump_to_event_index": 2},
                {"text": "B", "jump_to_event_index": 3},
            ],
        }, True),
        (0.0, "log", "skip me", False),
        (0.0, "log", "A path", False),
        (0.0, "log", "B path", False),
    ])

    story_system.tick(state)

    assert state.story_paused
    assert state.story_popup_mode == "choice"
    assert state.story_choices is not None
    assert len(state.story_choices) == 2

    story_system.choose(state, 0)

    assert state.story_event_index == 2
    assert not state.story_paused
    assert state.story_choices is None


def test_condition_jumps_based_on_flag():
    state = GameState()
    _reset_story(state, [
        (0.0, "flag", {"set": {"branch": "b"}}, False),
        (0.0, "condition", {
            "if": {"type": "flag", "key": "branch", "value": "a"},
            "then": 2,  # target one before desired event 3
            "else": 3,  # target one before desired event 4
        }, False),
        (0.0, "log", "never reached", False),
        (0.0, "log", "branch a", False),
        (0.0, "log", "branch b", False),
    ])

    story_system.tick(state)

    assert state.story_event_index == 5
    assert "branch b" in state.logs
    assert "branch a" not in state.logs


def test_condition_has_resources():
    state = GameState()
    state.scrap = 10
    _reset_story(state, [
        (0.0, "condition", {
            "if": {"type": "has_resources", "scrap": 5},
            "then": 1,  # target one before desired event 2
            "else": 2,  # target one before desired event 3
        }, False),
        (0.0, "log", "skip", False),
        (0.0, "log", "has enough", False),
        (0.0, "log", "too poor", False),
    ])

    story_system.tick(state)

    # The then branch is taken; zero-delay events continue to run afterwards.
    assert state.story_event_index == 4
    assert "has enough" in state.logs


def test_queued_story_starts_when_inactive():
    state = GameState()
    state.story_active = False
    state.story_events = []
    state.story_queue = [("queued", [
        (0.0, "unlock_tab", {"tab": TAB_POPULATION, "title": "人口", "text": "人口说明"}, True),
        (0.0, "log", "after", False),
    ])]

    # First tick only dequeues and starts the story.
    story_system.tick(state)
    assert state.story_active
    assert state.story_current_key == "queued"
    assert state.story_event_index == 0
    assert not state.story_paused

    # Second tick processes the first (blocking) event.
    story_system.tick(state)
    assert state.story_paused
    assert state.story_event_index == 1
    assert TAB_POPULATION in state.visible_tabs


def test_finish_story_starts_next_queued_story():
    state = GameState()
    _reset_story(state, [(0.0, "log", "current story", False)])
    state.story_queue = [("next", [
        (0.0, "unlock_tab", {"tab": TAB_POPULATION, "title": "人口", "text": "人口说明"}, True),
        (0.0, "log", "after", False),
    ])]

    story_system.tick(state)

    assert state.story_current_key == "next"
    assert state.story_event_index == 0
    assert state.story_active


def test_intro_finish_unlocks_materials_tab():
    state = GameState()
    _reset_story(state, [(0.0, "end_story", None, False)], key="intro")

    story_system.tick(state)

    assert not state.story_active
    assert state.story_current_key is None
    assert TAB_MATERIALS in state.visible_tabs
    assert "资源循环开始" in state.logs[-1]


def test_unknown_action_is_logged_and_not_blocking():
    state = GameState()
    _reset_story(state, [(0.0, "not_an_action", {}, False)])

    story_system.tick(state)

    assert any("未知动作" in log for log in state.logs)
    assert not state.story_paused
    assert state.story_event_index == 1
