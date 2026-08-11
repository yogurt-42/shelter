"""Shelter UI — materials tab: resources and items inventory."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    MAIN_AREA_Y,
    MAIN_AREA_HEIGHT,
    MINI_LOG_HEIGHT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_DIM,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
)


ROW_HEIGHT = 28
SECTION_PAD = 16


def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the materials inventory: resources with caps, then items with shared cap."""
    from shelter.data.items import get_item

    content_top = MAIN_AREA_Y
    content_h = MAIN_AREA_HEIGHT - MINI_LOG_HEIGHT
    content_rect = pygame.Rect(0, content_top, WINDOW_WIDTH, content_h)
    pygame.draw.rect(surface, COLOR_BG, content_rect)

    font_small = fonts["small"]
    font_normal = fonts["normal"]

    x_label = 20
    x_value = 220
    y = content_top + 12

    # ---- resources header ----
    header = font_normal.render("资源储备", True, COLOR_TEXT_BRIGHT)
    surface.blit(header, (x_label, y))
    y += ROW_HEIGHT + 4

    resources = [
        ("电力", int(state.power), int(state.max_power)),
        ("水", int(state.water), int(state.max_water)),
        ("食物", int(state.food), int(state.max_food)),
        ("废料", int(state.scrap), int(state.max_scrap)),
    ]

    for name, current, cap in resources:
        label = font_small.render(name, True, COLOR_TEXT_BRIGHT)
        surface.blit(label, (x_label, y))

        value_text = f"{current} / {cap}"
        value = font_small.render(value_text, True, COLOR_TEXT_BRIGHT)
        surface.blit(value, (x_value, y))
        y += ROW_HEIGHT

    # ---- divider ----
    y += SECTION_PAD // 2
    pygame.draw.line(surface, COLOR_BORDER, (x_label, y), (WINDOW_WIDTH - x_label, y))
    y += SECTION_PAD

    # ---- items header ----
    item_header = font_normal.render("物品", True, COLOR_TEXT_BRIGHT)
    surface.blit(item_header, (x_label, y))

    cap_text = f"{state.total_item_slots()} / {state.max_items}"
    cap_surf = font_small.render(cap_text, True, COLOR_TEXT_DIM)
    surface.blit(cap_surf, (x_value, y + 3))
    y += ROW_HEIGHT + 4

    if not state.items:
        empty = font_small.render("暂无物品", True, COLOR_TEXT_DIM)
        surface.blit(empty, (x_label, y))
        return

    for item_key, count in state.items.items():
        item = get_item(item_key)
        name = item["name"] if item else item_key
        label = font_small.render(name, True, COLOR_TEXT_BRIGHT)
        surface.blit(label, (x_label, y))

        count_text = f"x{count}"
        count_surf = font_small.render(count_text, True, COLOR_TEXT_BRIGHT)
        surface.blit(count_surf, (x_value, y))
        y += ROW_HEIGHT


def handle_click(pos: tuple, state) -> bool:
    """Materials tab has no click interactions yet."""
    return False
