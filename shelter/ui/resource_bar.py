"""Shelter UI — resource bar (4 resources in a single row)."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    TAB_BAR_HEIGHT,
    RESOURCE_BAR_HEIGHT,
    COLOR_RESOURCE_BG,
    COLOR_RESOURCE_LABEL,
    COLOR_RESOURCE_VALUE,
    COLOR_BORDER,
    FONT_SIZE_SMALL,
)


def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the resource bar."""
    y = TAB_BAR_HEIGHT
    bar_rect = pygame.Rect(0, y, WINDOW_WIDTH, RESOURCE_BAR_HEIGHT)
    pygame.draw.rect(surface, COLOR_RESOURCE_BG, bar_rect)
    pygame.draw.line(
        surface, COLOR_BORDER,
        (0, y + RESOURCE_BAR_HEIGHT - 1),
        (WINDOW_WIDTH, y + RESOURCE_BAR_HEIGHT - 1),
    )

    font = fonts["small"]

    resources = [
        ("电力", state.power, state.max_power),
        ("水",   state.water, state.max_water),
        ("食物", state.food,  state.max_food),
        ("废料", state.scrap, state.max_scrap),
    ]

    x = 16
    sep = "  |  "
    sep_surf = font.render(sep, True, COLOR_BORDER)

    for label, value, cap in resources:
        # label part
        label_part = f"{label}: "
        label_surf = font.render(label_part, True, COLOR_RESOURCE_LABEL)
        surface.blit(label_surf, (x, y + 6))

        # value part
        x += label_surf.get_width()
        if cap is not None:
            value_part = f"{int(value)}/{int(cap)}"
        else:
            value_part = f"{int(value)}"
        value_surf = font.render(value_part, True, COLOR_RESOURCE_VALUE)
        surface.blit(value_surf, (x, y + 6))
        x += value_surf.get_width()

        # separator
        surface.blit(sep_surf, (x, y + 6))
        x += sep_surf.get_width()
