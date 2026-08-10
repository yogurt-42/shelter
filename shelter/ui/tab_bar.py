"""Shelter UI — top tab bar (with show/hide support)."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    TAB_BAR_HEIGHT,
    TAB_STATUS,
    TAB_BUILD,
    TAB_POPULATION,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_TAB_ACTIVE_TEXT,
    COLOR_TAB_ACTIVE_UNDERLINE,
    COLOR_TAB_INACTIVE_TEXT,
    FONT_SIZE_SMALL,
)

ALL_TABS = [
    (TAB_STATUS, "状态"),
    (TAB_BUILD, "建筑"),
    (TAB_POPULATION, "人口"),
]


def _visible_tab_list(state) -> list:
    """Return currently visible tabs as [(key, label), ...]."""
    return [(k, lbl) for k, lbl in ALL_TABS if k in state.visible_tabs]


def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the tab bar — only visible tabs are rendered."""
    bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, TAB_BAR_HEIGHT)
    pygame.draw.rect(surface, COLOR_BG, bar_rect)
    pygame.draw.line(
        surface, COLOR_BORDER,
        (0, TAB_BAR_HEIGHT - 1), (WINDOW_WIDTH, TAB_BAR_HEIGHT - 1),
    )

    font = fonts["small"]
    x = 12

    for key, label in _visible_tab_list(state):
        is_active = (key == state.active_tab)
        color = COLOR_TAB_ACTIVE_TEXT if is_active else COLOR_TAB_INACTIVE_TEXT

        text = f"[ {label} ]"
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, (x, 6))

        if is_active:
            tw = text_surf.get_width()
            pygame.draw.line(
                surface, COLOR_TAB_ACTIVE_UNDERLINE,
                (x, TAB_BAR_HEIGHT - 4), (x + tw, TAB_BAR_HEIGHT - 4),
                width=2,
            )

        x += text_surf.get_width() + 20

    # elapsed time on the right
    elapsed = state.elapsed_seconds
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)
    time_text = f"运行 {days}天{hours}时{minutes}分"
    time_surf = font.render(time_text, True, COLOR_TAB_INACTIVE_TEXT)
    surface.blit(time_surf, (WINDOW_WIDTH - time_surf.get_width() - 12, 7))


def handle_click(pos: tuple, state) -> bool:
    """Handle tab bar click. Only visible tabs respond."""
    x, y = pos
    if y < 0 or y > TAB_BAR_HEIGHT:
        return False

    tab_x = 12
    font = pygame.font.SysFont("SimHei", FONT_SIZE_SMALL)
    for key, label in _visible_tab_list(state):
        text = f"[ {label} ]"
        text_surf = font.render(text, True, (255, 255, 255))
        tw = text_surf.get_width()
        if tab_x <= x <= tab_x + tw:
            if state.active_tab != key:
                state.active_tab = key
                return True
        tab_x += tw + 20

    return False


def get_first_visible(state) -> int:
    """Return the key of the first visible tab, or TAB_STATUS if all hidden."""
    tabs = _visible_tab_list(state)
    if tabs:
        return tabs[0][0]
    return TAB_STATUS
