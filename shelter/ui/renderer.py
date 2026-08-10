"""Shelter UI — main render dispatcher."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MAIN_AREA_Y,
    MAIN_AREA_HEIGHT,
    MINI_LOG_HEIGHT,
    MINI_LOG_BG,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_DIM,
    FONT_SIZE_SMALL,
    TAB_STATUS,
    TAB_BUILD,
    TAB_POPULATION,
)
from shelter.ui import tab_bar, resource_bar, status_tab, build_tab, console, popup, population_tab


def _draw_mini_log(surface: pygame.Surface, state, fonts: dict):
    """Draw the mini-log panel at the bottom of non-status tabs."""
    y = MAIN_AREA_Y + MAIN_AREA_HEIGHT - MINI_LOG_HEIGHT
    panel_rect = pygame.Rect(0, y, WINDOW_WIDTH, MINI_LOG_HEIGHT)
    pygame.draw.rect(surface, MINI_LOG_BG, panel_rect)

    pygame.draw.line(surface, COLOR_BORDER, (0, y), (WINDOW_WIDTH, y))

    font = fonts["small"]
    line_height = 19

    recent = state.logs[-3:] if len(state.logs) >= 3 else state.logs
    for i, text in enumerate(recent):
        prefix = "> "
        prefix_surf = font.render(prefix, True, COLOR_TEXT_DIM)
        surface.blit(prefix_surf, (12, y + 6 + i * line_height))

        max_chars = (WINDOW_WIDTH - 40) // 10
        if len(text) > max_chars:
            text = text[:max_chars - 2] + ".."
        text_surf = font.render(text, True, COLOR_TEXT_BRIGHT)
        surface.blit(text_surf, (12 + prefix_surf.get_width(), y + 6 + i * line_height))


def draw_all(surface: pygame.Surface, state, fonts: dict):
    """Clear and render all UI components."""
    surface.fill(COLOR_BG)

    # 1. tab bar
    tab_bar.draw(surface, state, fonts)

    # 2. resource bar (always visible)
    resource_bar.draw(surface, state, fonts)

    # 3. main area — switch by active tab
    if state.active_tab == TAB_STATUS:
        status_tab.draw(surface, state, fonts)
    elif state.active_tab == TAB_BUILD:
        build_tab.draw(surface, state, fonts)
        _draw_mini_log(surface, state, fonts)
    elif state.active_tab == TAB_POPULATION:
        population_tab.draw(surface, state, fonts)
        _draw_mini_log(surface, state, fonts)

    # 4. command console (always visible)
    console.draw(surface, state, fonts)

    # 5. popup overlay (drawn last, on top of everything)
    _draw_popup_overlay(surface, state, fonts)

    pygame.display.flip()


def _draw_popup_overlay(surface: pygame.Surface, state, fonts: dict):
    """Draw the active popup on top of all other UI."""
    if state.popup_type is None:
        return

    # semi-transparent dark backdrop
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    if state.popup_type == "build":
        popup.draw_build(surface, state, fonts)
    elif state.popup_type == "ruin_info":
        popup.draw_ruin_info(surface, state, fonts)
    elif state.popup_type == "room_info":
        popup.draw_room_info(surface, state, fonts)
    elif state.popup_type == "room_action":
        popup.draw_room_action(surface, state, fonts)
