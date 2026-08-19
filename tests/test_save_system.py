"""Tests for save_system.py."""

from pathlib import Path

from shelter.game_state import GameState
from shelter.systems import room_system
from shelter import save_system


def test_save_and_load_roundtrip(tmp_path):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    state = GameState()
    state.scrap = 42
    state.population = 5
    room_system.init_floors(state)

    msg = save_system.save_game(state, slot=1, saves_dir=saves_dir)
    assert "已保存" in msg

    loaded = save_system.load_game(slot=1, saves_dir=saves_dir)
    assert loaded is not None
    assert loaded.scrap == 42
    assert loaded.population == 5
    assert len(loaded.floors) == len(state.floors)


def test_load_empty_slot_returns_none(tmp_path):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    assert save_system.load_game(slot=1, saves_dir=saves_dir) is None


def test_list_saves_reads_metadata(tmp_path):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    state = GameState()
    state.population = 7
    save_system.save_game(state, slot=2, saves_dir=saves_dir)

    saves = save_system.list_saves(saves_dir=saves_dir)
    assert any(s["slot"] == 2 and s["population"] == 7 for s in saves)


def test_delete_save_removes_file(tmp_path):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    state = GameState()
    save_system.save_game(state, slot=3, saves_dir=saves_dir)
    assert (saves_dir / "slot_3.sav").exists()

    msg = save_system.delete_save(slot=3, saves_dir=saves_dir)
    assert "已删除" in msg
    assert not (saves_dir / "slot_3.sav").exists()


def test_invalid_slot_rejected():
    state = GameState()
    msg = save_system.save_game(state, slot=0)
    assert "无效槽位" in msg

    assert save_system.load_game(slot=0) is None
    assert "无效槽位" in save_system.delete_save(slot=99)


def test_save_migration_adds_missing_fields(tmp_path):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    # Save with current state, then simulate an old save by stripping new fields.
    state = GameState()
    save_system.save_game(state, slot=1, saves_dir=saves_dir)

    loaded = save_system.load_game(slot=1, saves_dir=saves_dir)
    assert hasattr(loaded, "story_popup_mode")
    assert hasattr(loaded, "story_choices")
    assert hasattr(loaded, "story_queue")
    assert hasattr(loaded, "story_flags")
    assert hasattr(loaded, "story_resume_tab")


def test_save_timestamps_resume_correctly(tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    import time

    fixed_now = 1_000_000.0
    monkeypatch.setattr(time, "time", lambda: fixed_now)

    state = GameState()
    state.elapsed_seconds = 123.0
    save_system.save_game(state, slot=1, saves_dir=saves_dir)

    loaded = save_system.load_game(slot=1, saves_dir=saves_dir)
    assert loaded.start_time == fixed_now - 123.0
    assert loaded.last_resource_tick == fixed_now
    assert loaded.last_event_time == fixed_now + 30.0
