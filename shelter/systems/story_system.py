"""Shelter — story system: decoupled narrative/event driver.

The GameState holds only runtime state (story_active, story_events, etc.).
This module reads story definitions from `data.stories` and drives them.

Public API:
    - play_story(state, story_key)      queue/start a story
    - tick(state)                       advance the active story each frame
    - resume_story(state)               resume after a blocking event
    - choose(state, choice_index)       handle a player choice
    - register_action(name, handler)    register custom event actions

Story event tuple:
    (delay_seconds, action, data, is_blocking)

Built-in actions:
    - "log"              : data = text string
    - "unlock_tab"       : data = {tab, title, text, log}
    - "unlock_blueprint" : data = {keys: [str], log}
    - "flag"             : data = {set: {key: value}, log}
    - "choice"           : data = {title, text, choices: [{text, jump_to_event_index}], log}
    - "condition"        : data = {if: condition_dict, then: event_index, else: event_index}
    - "end_story"        : data = None | {next_story: str}

Handlers receive (state, data) and return True if the event should block.
"""

import time
import random
from shelter.config import EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX, TAB_STATUS, TAB_MATERIALS


# ---------------------------------------------------------------------------
# Action registry
# ---------------------------------------------------------------------------

_ACTION_HANDLERS: dict[str, callable] = {}


def register_action(name: str, handler: callable):
    """Register a custom story action handler.

    handler(state, data) -> bool
        Return True if the event should pause the story and wait for player input.
    """
    _ACTION_HANDLERS[name] = handler


def _handler(name: str):
    return _ACTION_HANDLERS.get(name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def play_intro(state):
    """Convenience entry point for the opening story."""
    play_story(state, "intro")


def play_story(state, story_key: str):
    """Queue a story. If no story is active, start it immediately."""
    from shelter.data.stories import STORIES

    story = STORIES.get(story_key)
    if not story:
        return

    events = list(story.get("events", []))
    state.story_queue.append((story_key, events))
    if not getattr(state, "story_active", False):
        _start_next_story(state)


def tick(state):
    """Advance the currently active story by one frame."""
    if not getattr(state, "story_active", False) or getattr(state, "story_paused", False):
        # Try to start a queued story if nothing is active.
        if not getattr(state, "story_active", False) and getattr(state, "story_queue", []):
            _start_next_story(state)
        return

    now = time.time()
    elapsed = now - state.story_last_event_time

    while state.story_event_index < len(state.story_events):
        event = state.story_events[state.story_event_index]
        delay = event[0]
        if elapsed < delay:
            break

        blocking = _handle_event(state, event)
        state.story_event_index += 1
        state.story_last_event_time = now
        elapsed = 0.0

        if event[-1] or blocking:
            state.story_paused = True
            break

    if state.story_event_index >= len(state.story_events):
        _finish_story(state)


def resume_story(state):
    """Resume the active story after a blocking event (e.g. popup closed)."""
    state.story_paused = False
    state.story_pause_tab = None
    state.story_resume_tab = None
    state.story_choices = None
    state.story_last_event_time = time.time()


def choose(state, choice_index: int):
    """Handle a player choice from a "choice" event."""
    choices = getattr(state, "story_choices", None)
    if not choices or choice_index < 0 or choice_index >= len(choices):
        resume_story(state)
        return

    choice = choices[choice_index]
    jump = choice.get("jump_to_event_index")
    if jump is not None and 0 <= jump <= len(state.story_events):
        state.story_event_index = jump
    state.story_choices = None
    resume_story(state)


# ---------------------------------------------------------------------------
# Story queue / lifecycle
# ---------------------------------------------------------------------------

def _start_next_story(state):
    """Pop the next queued story and make it active."""
    queue = getattr(state, "story_queue", [])
    if not queue:
        state.story_active = False
        return

    key, events = queue.pop(0)
    state.story_active = True
    state.story_current_key = key
    state.story_events = events
    state.story_event_index = 0
    state.story_paused = False
    state.story_pause_tab = None
    state.story_resume_tab = None
    state.story_popup_title = ""
    state.story_popup_text = ""
    state.story_popup_mode = "info"
    state.story_choices = None
    state.story_last_event_time = time.time()


def _finish_story(state):
    """Clean up the active story and start the next queued one if any."""
    state.story_active = False
    state.story_paused = False
    state.story_pause_tab = None
    state.story_resume_tab = None
    state.story_choices = None

    # If this was the intro, start normal gameplay systems.
    if getattr(state, "story_current_key", None) == "intro":
        now = time.time()
        state.last_resource_tick = now
        state.last_event_time = now + random.uniform(EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX)
        state.unlock_tab(TAB_MATERIALS)
        state.add_log("资源循环开始。避难所状态：低功率运行。")

    state.story_current_key = None

    if getattr(state, "story_queue", []):
        _start_next_story(state)


# ---------------------------------------------------------------------------
# Event handling
# ---------------------------------------------------------------------------

def _handle_event(state, event):
    """Execute a single story event. Returns True if blocking."""
    _delay, action, data, _blocking = event

    handler = _ACTION_HANDLERS.get(action)
    if handler is None:
        # Unknown action: log and continue.
        state.add_log(f"[剧情系统] 未知动作: {action}")
        return False

    return bool(handler(state, data))


# ---------------------------------------------------------------------------
# Built-in action handlers
# ---------------------------------------------------------------------------

def _action_log(state, data):
    state.add_log(data)
    return False


def _action_unlock_tab(state, data):
    tab = data["tab"]
    title = data.get("title", "")
    text = data.get("text", "")
    log_line = data.get("log")

    state.unlock_tab(tab)
    state.story_pause_tab = tab
    state.story_resume_tab = TAB_STATUS
    state.story_popup_title = title
    state.story_popup_text = text
    state.story_popup_mode = "info"
    state.story_choices = None
    if log_line:
        state.add_log(log_line)
    return True


def _action_unlock_blueprint(state, data):
    keys = data.get("keys", [])
    if isinstance(keys, str):
        keys = [keys]
    state.unlock_blueprint(*keys)
    log_line = data.get("log")
    if log_line:
        state.add_log(log_line)
    return False


def _action_flag(state, data):
    flags = data.get("set", {})
    for key, value in flags.items():
        state.story_flags[key] = value
    log_line = data.get("log")
    if log_line:
        state.add_log(log_line)
    return False


def _action_choice(state, data):
    title = data.get("title", "")
    text = data.get("text", "")
    choices = data.get("choices", [])
    log_line = data.get("log")

    state.story_pause_tab = None
    state.story_popup_title = title
    state.story_popup_text = text
    state.story_popup_mode = "choice"
    state.story_choices = choices
    if log_line:
        state.add_log(log_line)
    return True


def _action_condition(state, data):
    cond = data.get("if", {})
    then_idx = data.get("then")
    else_idx = data.get("else")

    matched = _evaluate_condition(state, cond)
    target = then_idx if matched else else_idx
    if target is not None and 0 <= target <= len(state.story_events):
        state.story_event_index = target
    return False


def _action_end_story(state, data):
    _finish_story(state)
    # Queue next story if requested.
    if isinstance(data, dict):
        next_key = data.get("next_story")
        if next_key:
            play_story(state, next_key)
    return False


def _evaluate_condition(state, cond: dict) -> bool:
    """Evaluate a simple condition dict."""
    ctype = cond.get("type", "")

    if ctype == "flag":
        key = cond.get("key")
        expected = cond.get("value", True)
        return state.story_flags.get(key) == expected

    if ctype == "has_resources":
        from shelter.systems import room_system
        cost = {k: v for k, v in cond.items() if k != "type"}
        can, _ = room_system.check_resources(state, cost)
        return can

    if ctype == "min_population":
        return state.population >= cond.get("value", 0)

    # Unknown condition defaults to True to avoid blocking stories.
    return True


# ---------------------------------------------------------------------------
# Register built-ins
# ---------------------------------------------------------------------------

def _register_defaults():
    register_action("log", _action_log)
    register_action("unlock_tab", _action_unlock_tab)
    register_action("unlock_blueprint", _action_unlock_blueprint)
    register_action("flag", _action_flag)
    register_action("choice", _action_choice)
    register_action("condition", _action_condition)
    register_action("end_story", _action_end_story)


_register_defaults()
