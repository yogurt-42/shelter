"""Tests for ui/console.py command parsing (no pygame surface needed)."""

import pytest
from shelter.game_state import GameState
from shelter.ui import console
from shelter.config import TAB_BUILD


def test_execute_status_command():
    state = GameState()
    lines = console._execute("/status", state)
    assert any("电力" in line for line in lines)


def test_execute_unknown_player_command():
    state = GameState()
    lines = console._execute("/foobar", state)
    assert any("Unknown command" in line for line in lines)


def test_execute_non_command_input():
    state = GameState()
    lines = console._execute("hello", state)
    assert any("Unrecognized input" in line for line in lines)


def test_admin_infinite_and_enough():
    state = GameState()

    lines = console._execute("//i am infinite", state)
    assert state.infinite_resources
    assert any("无限资源" in line for line in lines)

    lines = console._execute("//it is enough", state)
    assert not state.infinite_resources
    assert any("退出" in line for line in lines)


def test_admin_full_speed():
    state = GameState()
    state.floors = [[{
        "state": 3,
        "room_type": "power_1",
        "action_type": "build",
        "build_end_time": 100.0,
        "revealed": True,
        "void": False,
    }]]

    lines = console._execute("//full speed", state)
    assert state.full_speed
    assert state.floors[0][0]["build_end_time"] == 0
    assert any("极速建造" in line for line in lines)


def test_admin_give_unknown_item():
    state = GameState()
    lines = console._execute("//give no_such_item", state)
    assert any("未知物品" in line for line in lines)


def test_admin_give_known_item():
    state = GameState()
    lines = console._execute("//give test_item_a 2", state)
    assert state.total_item_slots() > 0
    assert any("测试物品 A" in line for line in lines)


def test_admin_hide_and_show_tab():
    state = GameState()
    state.visible_tabs.add(TAB_BUILD)

    lines = console._execute("//hide build", state)
    assert TAB_BUILD not in state.visible_tabs
    assert any("hidden" in line for line in lines)

    lines = console._execute("//show build", state)
    assert TAB_BUILD in state.visible_tabs
    assert any("shown" in line for line in lines)


def test_admin_tabs_lists_visible():
    state = GameState()
    lines = console._execute("//tabs", state)
    assert any("status" in line for line in lines)


def test_admin_unknown_command():
    state = GameState()
    lines = console._execute("//unknown", state)
    assert any("Unknown admin command" in line for line in lines)


def test_save_and_load_commands(tmp_path, monkeypatch):
    import shelter.save_system as save_system

    # Redirect default saves directory to a temp location for this test.
    monkeypatch.setattr(save_system, "SAVES_DIR", str(tmp_path))

    state = GameState()
    state.scrap = 100

    save_msg = console._cmd_save(state, "1")
    assert "已保存" in save_msg[0]

    # Mutate state, then load and verify it is restored.
    state.scrap = 0
    load_msg = console._cmd_load(state, "1")
    assert "读取存档" in load_msg[0]
    assert state.scrap == 100
