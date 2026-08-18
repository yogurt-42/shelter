"""Shelter — entry point. Initializes Pygame and runs the main loop."""

import sys
import time
import pygame
from shelter.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    FPS,
    FONT_NAME_CJK,
    FONT_NAME_MONO,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
    FONT_SIZE_LARGE,
    TAB_STATUS,
    TAB_BUILD,
    TAB_POPULATION,
    TAB_MATERIALS,
    ROOM_STATE_BUILDING,
    ROOM_STATE_CLEARING,
)
from shelter.game_state import GameState
from shelter.save_system import list_saves
from shelter.systems import resource_system, event_system, room_system, story_system
from shelter.ui.renderer import draw_all
from shelter.ui import tab_bar, build_tab, status_tab, console, popup, population_tab, materials_tab


def _next_visible_tab(state) -> int:
    """Return the key of the next visible tab for Tab-key cycling."""
    visible = [k for k, _ in tab_bar.ALL_TABS if k in state.visible_tabs]
    if not visible:
        return TAB_STATUS
    try:
        idx = visible.index(state.active_tab)
        return visible[(idx + 1) % len(visible)]
    except ValueError:
        return visible[0]


def init_fonts() -> dict:
    fonts = {}
    for size_key, size_val in [
        ("small", FONT_SIZE_SMALL),
        ("normal", FONT_SIZE_NORMAL),
        ("large", FONT_SIZE_LARGE),
    ]:
        try:
            fonts[size_key] = pygame.font.SysFont(FONT_NAME_CJK, size_val)
        except Exception:
            fonts[size_key] = pygame.font.SysFont(FONT_NAME_MONO, size_val)
    return fonts


# ---- popup click dispatch ----

_POPUP_HANDLERS = {
    "build": popup.handle_build_click,
    "ruin_info": popup.handle_ruin_info_click,
    "room_info": popup.handle_room_info_click,
    "room_action": popup.handle_room_action_click,
    "story": popup.handle_story_click,
}


def _handle_popup_click(pos: tuple, state) -> bool:
    """Route a click to the active popup's handler."""
    if state.popup_type is None:
        return False
    handler = _POPUP_HANDLERS.get(state.popup_type)
    if handler:
        return handler(pos, state)
    return False


# ---- construction tick ----

def _tick_construction(state):
    """Check all rooms for completed construction timers."""
    now = time.time()
    for f in range(len(state.floors)):
        for r in range(len(state.floors[f])):
            slot = state.floors[f][r]
            end_time = slot.get("build_end_time")
            if end_time is None:
                continue
            # full_speed: fast-forward anything still waiting
            if getattr(state, "full_speed", False) and now < end_time:
                slot["build_end_time"] = 0
                end_time = 0
            if now >= end_time and slot.get("action_type"):
                action = slot["action_type"]
                room_system.complete_construction(state, f, r)
                if action == "building":
                    from shelter.data.rooms import get_room
                    tmpl = get_room(slot.get("room_type", ""))
                    name = tmpl["name"] if tmpl else slot.get("room_type", "?")
                    state.add_log(f"第{f+1}层 房间{r+1}：{name} 建造完成！")
                elif action == "clearing":
                    state.add_log(f"第{f+1}层 房间{r+1}：废墟清理完成，现在可以建造了。")


# ---- main ----

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    fonts = init_fonts()
    state = GameState()

    # notify if save files exist (after intro so it doesn't clutter opening logs)
    saves = list_saves()
    if saves:
        state.add_log(f"检测到 {len(saves)} 个存档。输入 /saves 查看，/load [槽位] 读取。")

    running = True
    while running:
        dt = clock.tick(FPS)

        # ---- events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                # popup overlay eats clicks first
                if state.popup_type and event.button == 1:
                    _handle_popup_click(pos, state)
                    continue

                if event.button == 1:  # left click
                    if tab_bar.handle_click(pos, state):
                        # Story sequence: if a newly-unlocked tab is clicked, show its popup.
                        if (
                            state.story_active
                            and state.story_paused
                            and state.story_pause_tab == state.active_tab
                        ):
                            state.popup_type = "story"
                            state.popup_floor = 0
                            state.popup_room = 0
                    elif state.active_tab == TAB_BUILD:
                        build_tab.handle_mouse_down(pos, state)
                    elif state.active_tab == TAB_POPULATION:
                        population_tab.handle_click(pos, state)
                    elif state.active_tab == TAB_MATERIALS:
                        materials_tab.handle_click(pos, state)

                elif event.button == 3:  # right click
                    if state.active_tab == TAB_BUILD:
                        build_tab.handle_right_click(pos, state)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if state.active_tab == TAB_BUILD:
                        build_tab.handle_mouse_up(event.pos, state)

            elif event.type == pygame.MOUSEMOTION:
                if state.active_tab == TAB_BUILD:
                    build_tab.handle_mouse_motion(event.pos, state)

            elif event.type == pygame.MOUSEWHEEL:
                if state.active_tab == TAB_STATUS:
                    status_tab.handle_wheel(event.y, state)
                elif state.active_tab == TAB_BUILD:
                    build_tab.handle_wheel(event.y, state)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state.popup_type:
                        if state.popup_type == "story":
                            state.close_popup()
                            story_system.resume_story(state)
                        else:
                            state.close_popup()
                    else:
                        state.console_input = ""
                elif event.key == pygame.K_TAB:
                    state.active_tab = _next_visible_tab(state)
                elif event.key == pygame.K_END:
                    state.log_scroll_offset = 0
                else:
                    console.handle_key(event, state)

        # ---- game systems tick ----
        state.update_time()

        # construction timers
        _tick_construction(state)

        if not state.story_active:
            # resource production (passive scrap + room production)
            res_msgs = resource_system.tick(state)
            for msg in res_msgs:
                state.add_log_and_track(msg)

            evt_msgs = event_system.tick(state)
            for msg in evt_msgs:
                state.add_log_and_track(msg)

        # ---- render ----
        draw_all(screen, state, fonts)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
