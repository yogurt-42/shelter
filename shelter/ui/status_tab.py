"""Shelter UI — status tab (log viewer with mouse-wheel scroll)."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    MAIN_AREA_Y,
    MAIN_AREA_HEIGHT,
    COLOR_BG,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_DIM,
    FONT_SIZE_SMALL,
)

LINE_HEIGHT = 20


def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the status tab log area. Scroll offset controlled by state.log_scroll_offset."""
    area_rect = pygame.Rect(0, MAIN_AREA_Y, WINDOW_WIDTH, MAIN_AREA_HEIGHT)
    pygame.draw.rect(surface, COLOR_BG, area_rect)

    font = fonts["small"]
    visible_lines = MAIN_AREA_HEIGHT // LINE_HEIGHT
    logs = state.logs
    total_lines = len(logs)

    # clamp offset
    max_offset = max(0, total_lines - visible_lines)
    offset = min(state.log_scroll_offset, max_offset)

    # compute start index from the bottom
    start_idx = max(0, total_lines - visible_lines - offset)

    y = MAIN_AREA_Y + 4
    for i in range(start_idx, min(start_idx + visible_lines, total_lines)):
        prefix = "> "
        prefix_surf = font.render(prefix, True, COLOR_TEXT_DIM)
        surface.blit(prefix_surf, (12, y))

        text = logs[i]
        max_chars = (WINDOW_WIDTH - 40) // 10
        if len(text) > max_chars:
            text = text[:max_chars - 2] + ".."

        text_surf = font.render(text, True, COLOR_TEXT_BRIGHT)
        surface.blit(text_surf, (12 + prefix_surf.get_width(), y))
        y += LINE_HEIGHT

    # scroll indicator
    if offset > 0:
        hint = f"[ scrolled {offset} lines — scroll or press End to return ]"
        hint_surf = font.render(hint, True, COLOR_TEXT_DIM)
        surface.blit(
            hint_surf,
            (WINDOW_WIDTH - hint_surf.get_width() - 16,
             MAIN_AREA_Y + MAIN_AREA_HEIGHT - LINE_HEIGHT - 4),
        )


def handle_wheel(y_offset: int, state) -> bool:
    """Handle mouse wheel: positive = scroll back, negative = toward latest."""
    state.log_scroll_offset += y_offset
    if state.log_scroll_offset < 0:
        state.log_scroll_offset = 0
    return True


def handle_click(pos: tuple, state) -> bool:
    """Status tab has no click interactions."""
    return False
