"""Shelter UI — population tab: assign workers to job types aggregated across rooms."""

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
    COLOR_TEXT_MID,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
)


CARD_BG = (18, 18, 18)
CARD_HOVER = (40, 40, 40)
CARD_HEIGHT = 52
CARD_PAD = 8
BTN_W = 24
BTN_H = 22


def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the population assignment panel."""
    from shelter.data.job_types import JOB_DEFINITIONS

    content_top = MAIN_AREA_Y
    content_h = MAIN_AREA_HEIGHT - MINI_LOG_HEIGHT
    content_rect = pygame.Rect(0, content_top, WINDOW_WIDTH, content_h)
    pygame.draw.rect(surface, COLOR_BG, content_rect)

    font = fonts["small"]
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # ---- top summary bar ----
    header_y = content_top + 8
    free = state.free_workers
    assigned = state.assigned_workers_total

    summary = f"总人口: {state.population}    空闲: {free}    在岗: {assigned}"
    summary_surf = font.render(summary, True, COLOR_TEXT_BRIGHT)
    surface.blit(summary_surf, (16, header_y))

    # separator
    sep_y = header_y + 26
    pygame.draw.line(surface, COLOR_BORDER, (12, sep_y), (WINDOW_WIDTH - 12, sep_y))

    # ---- job type list ----
    # Collect all job types that have slot capacity > 0
    active_jobs = []
    for jt_key, jt_data in JOB_DEFINITIONS.items():
        total_slots = state.total_job_slots(jt_key)
        if total_slots > 0:
            current = state.job_assignment.get(jt_key, 0)
            active_jobs.append((jt_key, jt_data, total_slots, current))

    list_y = sep_y + 8

    if not active_jobs:
        hint = font.render("尚未建造可提供岗位的房间", True, COLOR_TEXT_DIM)
        surface.blit(hint, (16, list_y + 8))
        return

    for i, (jt_key, jt_data, total_slots, current) in enumerate(active_jobs):
        card_y = list_y + i * (CARD_HEIGHT + CARD_PAD)
        card_rect = pygame.Rect(12, card_y, WINDOW_WIDTH - 24, CARD_HEIGHT)

        # card background
        hover = card_rect.collidepoint(mouse_x, mouse_y)
        bg = CARD_HOVER if hover else CARD_BG
        pygame.draw.rect(surface, bg, card_rect)
        pygame.draw.rect(surface, COLOR_BORDER, card_rect, width=1)

        cx, cy = card_rect.x, card_rect.y

        # job name
        name_surf = font.render(jt_data["name"], True, COLOR_TEXT_BRIGHT)
        surface.blit(name_surf, (cx + 10, cy + 6))

        # slot count
        slot_text = f"{current}/{total_slots}"
        slot_surf = font.render(slot_text, True, COLOR_TEXT_BRIGHT)
        surface.blit(slot_surf, (cx + 190, cy + 6))

        # --- − button ---
        btn_minus = pygame.Rect(cx + 260, cy + 4, BTN_W, BTN_H)
        can_minus = current > 0
        _draw_btn(surface, btn_minus, "-", font, can_minus, mouse_x, mouse_y)

        # --- + button ---
        btn_plus = pygame.Rect(cx + 290, cy + 4, BTN_W, BTN_H)
        can_plus = free > 0 and current < total_slots
        _draw_btn(surface, btn_plus, "+", font, can_plus, mouse_x, mouse_y)

        # production / consumption info (dim, below name)
        info_parts = []
        for res, rate in jt_data.get("production", {}).items():
            info_parts.append(f"{res}+{rate}/s/人")
        for res, rate in jt_data.get("consumption", {}).items():
            info_parts.append(f"{res}−{rate}/s/人")

        info_text = "  ".join(info_parts) if info_parts else jt_data.get("description", "")
        info_surf = font.render(info_text, True, COLOR_TEXT_DIM)
        surface.blit(info_surf, (cx + 10, cy + 28))


def _draw_btn(surface, rect, label, font, enabled, mx, my):
    """Draw a small square +/- button."""
    if enabled:
        hover = rect.collidepoint(mx, my)
        btn_bg = (80, 80, 80) if hover else (50, 50, 50)
        text_color = COLOR_TEXT_BRIGHT
    else:
        btn_bg = (30, 30, 30)
        text_color = COLOR_TEXT_DIM

    pygame.draw.rect(surface, btn_bg, rect, border_radius=2)
    pygame.draw.rect(surface, COLOR_BORDER, rect, width=1, border_radius=2)

    label_surf = font.render(label, True, text_color)
    lx = rect.x + (rect.width - label_surf.get_width()) // 2
    ly = rect.y + (rect.height - label_surf.get_height()) // 2 - 1
    surface.blit(label_surf, (lx, ly))

    return rect


def handle_click(pos: tuple, state) -> bool:
    """Handle +/- button clicks on the population tab."""
    from shelter.data.job_types import JOB_DEFINITIONS

    x, y = pos
    content_top = MAIN_AREA_Y
    content_h = MAIN_AREA_HEIGHT - MINI_LOG_HEIGHT
    if y < content_top or y > content_top + content_h:
        return False

    free = state.free_workers

    # Collect active jobs (same logic as draw)
    active_jobs = []
    for jt_key, jt_data in JOB_DEFINITIONS.items():
        total_slots = state.total_job_slots(jt_key)
        if total_slots > 0:
            current = state.job_assignment.get(jt_key, 0)
            active_jobs.append((jt_key, jt_data, total_slots, current))

    header_y = content_top + 8
    sep_y = header_y + 26
    list_y = sep_y + 8

    for i, (jt_key, jt_data, total_slots, current) in enumerate(active_jobs):
        card_y = list_y + i * (CARD_HEIGHT + CARD_PAD)
        cx = 12

        btn_minus = pygame.Rect(cx + 260, card_y + 4, BTN_W, BTN_H)
        btn_plus = pygame.Rect(cx + 290, card_y + 4, BTN_W, BTN_H)

        if btn_minus.collidepoint(x, y) and current > 0:
            state.unassign_worker(jt_key)
            return True

        if btn_plus.collidepoint(x, y) and free > 0 and current < total_slots:
            state.assign_worker(jt_key)
            return True

    return False
