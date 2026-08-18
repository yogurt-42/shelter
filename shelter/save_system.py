"""Shelter — save/load system using pickle serialization."""

import os
import pickle
import time
import dataclasses
from dataclasses import fields
from shelter.game_state import GameState

SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
MAX_SLOTS = 3


def _ensure_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)


def _slot_path(slot: int) -> str:
    return os.path.join(SAVES_DIR, f"slot_{slot}.sav")


def save_game(state: GameState, slot: int) -> str:
    """Save current game to a slot. Returns a status message."""
    if not 1 <= slot <= MAX_SLOTS:
        return f"无效槽位: {slot}（可用 1-{MAX_SLOTS}）"
    _ensure_dir()
    data = {
        "slot": slot,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "game_days": state.elapsed_days,
        "game_hours": state.elapsed_hours,
        "game_minutes": state.elapsed_minutes,
        "population": state.population,
        "state": state,
    }
    with open(_slot_path(slot), "wb") as f:
        pickle.dump(data, f)
    return f"已保存至槽位 {slot}。"


def load_game(slot: int) -> GameState | None:
    """Load a GameState from a slot. Returns None if slot is empty or invalid."""
    if not 1 <= slot <= MAX_SLOTS:
        return None
    path = _slot_path(slot)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = pickle.load(f)
    state = data["state"]
    # Ensure backward compatibility: add missing fields with defaults
    for fld in fields(GameState):
        if not hasattr(state, fld.name):
            setattr(state, fld.name, fld.default_factory() if fld.default_factory is not dataclasses.MISSING else fld.default)

    # Migrate old intro_* fields to story_* fields (pre-2026-08-18 saves)
    _intro_to_story = {
        "intro_active": "story_active",
        "intro_current_key": "story_current_key",
        "intro_event_index": "story_event_index",
        "intro_events": "story_events",
        "intro_paused": "story_paused",
        "intro_pause_tab": "story_pause_tab",
        "intro_last_event_time": "story_last_event_time",
        "intro_tutorial_title": "story_popup_title",
        "intro_tutorial_text": "story_popup_text",
    }
    for old_key, new_key in _intro_to_story.items():
        if hasattr(state, old_key) and not getattr(state, new_key, None):
            old_val = getattr(state, old_key)
            if old_val is not None:
                setattr(state, new_key, old_val)
    for default_key, default_val in [
        ("story_popup_mode", "info"),
        ("story_choices", None),
        ("story_queue", []),
        ("story_flags", {}),
    ]:
        if not hasattr(state, default_key):
            setattr(state, default_key, default_val)

    # Adjust timing so game clock resumes from saved elapsed time
    state.start_time = time.time() - state.elapsed_seconds
    state.last_resource_tick = time.time()
    state.last_event_time = time.time() + 30.0
    return state


def list_saves() -> list[dict]:
    """Return metadata for all existing save slots."""
    result = []
    for slot in range(1, MAX_SLOTS + 1):
        path = _slot_path(slot)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            result.append({
                "slot": data.get("slot", slot),
                "saved_at": data.get("saved_at", "?"),
                "game_days": data.get("game_days", 0),
                "game_hours": data.get("game_hours", 0),
                "game_minutes": data.get("game_minutes", 0),
                "population": data.get("population", 0),
            })
        except Exception:
            continue
    return result


def delete_save(slot: int) -> str:
    """Delete a save slot. Returns a status message."""
    if not 1 <= slot <= MAX_SLOTS:
        return f"无效槽位: {slot}（可用 1-{MAX_SLOTS}）"
    path = _slot_path(slot)
    if not os.path.exists(path):
        return f"槽位 {slot} 为空，无需删除。"
    os.remove(path)
    return f"已删除槽位 {slot} 的存档。"
