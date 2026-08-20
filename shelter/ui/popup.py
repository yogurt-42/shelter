"""Shelter UI — popup overlay system (build / ruin / room info / room action / tutorial)."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    POPUP_WIDTH,
    POPUP_MAX_HEIGHT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_BORDER_LIGHT,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MID,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
)
from shelter.systems import room_system

POPUP_BG = (22, 22, 22)
POPUP_HEADER_BG = (30, 30, 30)
POPUP_ROW_HOVER = (50, 50, 50)
POPUP_ROW_HEIGHT = 32
POPUP_CARD_GAP = 4     # vertical gap between room cards
POPUP_PAD = 12
POPUP_BORDER_WIDTH = 1


# ============================================================
# Drawing helpers
# ============================================================

BODY_TOP_PAD = 6
BODY_BOTTOM_PAD = 8
TITLE_BAR_HEIGHT = 36


def _popup_rect() -> pygame.Rect:
    """Return a fixed-height popup rect centered on screen."""
    x = (WINDOW_WIDTH - POPUP_WIDTH) // 2
    y = (WINDOW_HEIGHT - POPUP_MAX_HEIGHT) // 2
    return pygame.Rect(x, y, POPUP_WIDTH, POPUP_MAX_HEIGHT)


def _body_rect(rect: pygame.Rect) -> pygame.Rect:
    """Scrollable body area below the title bar."""
    return pygame.Rect(
        rect.x + 4,
        rect.y + TITLE_BAR_HEIGHT + BODY_TOP_PAD,
        rect.width - 8,
        rect.height - TITLE_BAR_HEIGHT - BODY_TOP_PAD - BODY_BOTTOM_PAD,
    )


def _clamp_scroll(state, content_h: int):
    """Clamp popup scroll offset to the actual content height."""
    body = _body_rect(_popup_rect())
    max_scroll = max(0, content_h - body.height)
    state.popup_scroll_offset = max(0, min(state.popup_scroll_offset, max_scroll))


def _start_scroll(surface: pygame.Surface, rect: pygame.Rect, state, content_h: int) -> pygame.Rect:
    """Begin a scrollable drawing region. Returns the body rect."""
    _clamp_scroll(state, content_h)
    body = _body_rect(rect)
    surface.set_clip(body)
    return body


def _end_scroll(surface: pygame.Surface):
    """Restore the drawing clip region."""
    surface.set_clip(None)


def _content_start_y(rect: pygame.Rect) -> int:
    """Y position where popup body content begins (below title bar)."""
    return rect.y + TITLE_BAR_HEIGHT + BODY_TOP_PAD


def _draw_popup_frame(surface: pygame.Surface, rect: pygame.Rect):
    """Draw background + border for a popup."""
    pygame.draw.rect(surface, POPUP_BG, rect)
    pygame.draw.rect(surface, COLOR_BORDER, rect, POPUP_BORDER_WIDTH)


def _draw_title(surface: pygame.Surface, rect: pygame.Rect, title: str, font):
    """Draw popup title bar."""
    header_rect = pygame.Rect(rect.x, rect.y, rect.width, TITLE_BAR_HEIGHT)
    pygame.draw.rect(surface, POPUP_HEADER_BG, header_rect)
    title_surf = font.render(title, True, COLOR_TEXT_BRIGHT)
    surface.blit(title_surf, (rect.x + POPUP_PAD, rect.y + 8))
    # close hint
    hint_surf = font.render("[Esc 关闭]", True, COLOR_TEXT_DIM)
    surface.blit(hint_surf, (rect.right - hint_surf.get_width() - POPUP_PAD, rect.y + 8))


def _draw_hline(surface: pygame.Surface, y: int, x1: int, x2: int):
    """Draw a thin horizontal separator line."""
    pygame.draw.line(surface, (40, 40, 40), (x1, y), (x2, y))


def _job_info_text(tmpl: dict) -> str:
    """Return a concise Chinese string describing room jobs and rates."""
    from shelter.data.job_types import get_job

    job_type = tmpl.get("job_type")
    if not job_type:
        return "岗位：无"

    jt = get_job(job_type)
    job_name = jt["name"] if jt else job_type
    slots = tmpl.get("job_slots", 0)

    parts = []
    for k, v in tmpl.get("production_per_day", {}).items():
        parts.append(f"{room_system.res_cn(k)}+{v}/天/人")
    for k, v in tmpl.get("consumption_per_day", {}).items():
        parts.append(f"{room_system.res_cn(k)}-{v}/天/人")

    rate_text = "  ".join(parts) if parts else "无产出"
    return f"岗位：{job_name} ×{slots}  ({rate_text})"


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    """Wrap text into lines that fit within max_width."""
    if not text:
        return [""]
    words = []
    for ch in text:
        words.append(ch)
    lines = []
    current = ""
    for word in words:
        test = current + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if not lines:
        lines.append("")
    return lines

def _row_hover(rect: pygame.Rect, row_idx: int, mx: int, my: int, row_h: int = POPUP_ROW_HEIGHT) -> bool:
    row_y = _content_start_y(rect) + row_idx * row_h
    row_rect = pygame.Rect(rect.x + 4, row_y, rect.width - 8, row_h)
    return row_rect.collidepoint(mx, my)


# ============================================================
# Build popup (left-click empty slot)
# ============================================================

# Each room card: title row (clickable) + desc row + job row + gap
BUILD_ENTRY_HEIGHT = POPUP_ROW_HEIGHT * 3 + POPUP_CARD_GAP


def draw_build(surface: pygame.Surface, state, fonts: dict):
    """Draw the room construction selection popup — card layout."""
    from shelter.data.rooms import list_buildable

    rooms = list_buildable(state)
    n = len(rooms)
    content_h = TITLE_BAR_HEIGHT + BODY_TOP_PAD + n * BUILD_ENTRY_HEIGHT + 12
    state.popup_content_height = content_h
    rect = _popup_rect()

    _draw_popup_frame(surface, rect)
    font = fonts["small"]
    _draw_title(surface, rect, "建造房间", font)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    start_y = _content_start_y(rect) - state.popup_scroll_offset

    _start_scroll(surface, rect, state, content_h)

    for i, tmpl in enumerate(rooms):
        entry_top = start_y + i * BUILD_ENTRY_HEIGHT

        # ---- title row (highlight if hover) ----
        title_y = entry_top
        title_rect = pygame.Rect(rect.x + 8, title_y, rect.width - 16, POPUP_ROW_HEIGHT)
        hover = title_rect.collidepoint(mouse_x, mouse_y)
        if hover:
            pygame.draw.rect(surface, POPUP_ROW_HOVER, title_rect, border_radius=2)

        # room name (bright, large)
        name_surf = font.render(tmpl["name"], True, COLOR_TEXT_BRIGHT)
        surface.blit(name_surf, (title_rect.x + 4, title_rect.y + 6))

        # cost + time (right-aligned)
        cost_str = room_system.cost_cn(tmpl["build_cost"])
        meta_text = f"[{cost_str}]  {tmpl['build_time']}s"
        meta_surf = font.render(meta_text, True, COLOR_TEXT_MID)
        surface.blit(meta_surf, (title_rect.right - meta_surf.get_width() - 4, title_rect.y + 6))

        # ---- desc row ----
        desc_y = entry_top + POPUP_ROW_HEIGHT
        desc_surf = font.render(tmpl["description"], True, COLOR_TEXT_DIM)
        surface.blit(desc_surf, (rect.x + 16, desc_y + 6))

        # ---- job row ----
        job_y = entry_top + POPUP_ROW_HEIGHT * 2
        job_surf = font.render(_job_info_text(tmpl), True, COLOR_TEXT_MID)
        surface.blit(job_surf, (rect.x + 16, job_y + 6))

        # ---- separator between cards ----
        if i < n - 1:
            sep_y = entry_top + BUILD_ENTRY_HEIGHT - 1
            _draw_hline(surface, sep_y, rect.x + 12, rect.right - 12)

    _end_scroll(surface)


def handle_build_click(pos: tuple, state) -> bool:
    """Handle click inside the build popup. Returns True if an action was taken."""
    from shelter.data.rooms import list_buildable

    rooms = list_buildable(state)
    n = len(rooms)
    rect = _popup_rect()
    x, y = pos

    if not rect.collidepoint(x, y):
        state.close_popup()
        return False

    start_y = _content_start_y(rect) - state.popup_scroll_offset

    for i, tmpl in enumerate(rooms):
        entry_top = start_y + i * BUILD_ENTRY_HEIGHT
        title_rect = pygame.Rect(rect.x + 8, entry_top, rect.width - 16, POPUP_ROW_HEIGHT)
        if title_rect.collidepoint(x, y):
            cost = tmpl["build_cost"]
            can, failures = room_system.check_resources(state, cost)
            if not can:
                for msg in failures:
                    state.add_log(msg)
                state.close_popup()
                return True
            room_system.deduct_resources(state, cost)
            room_system.start_building(state, state.popup_floor, state.popup_room,
                                       tmpl["key"], tmpl["build_time"])
            state.add_log(f"开始建造 {tmpl['name']}，预计 {tmpl['build_time']} 秒后完工。")
            state.close_popup()
            return True

    return False


# ============================================================
# Ruin info popup (left-click ruin slot)
# ============================================================

_last_button_rect: pygame.Rect | None = None


def draw_ruin_info(surface: pygame.Surface, state, fonts: dict):
    """Draw ruin information and clearance option."""
    from shelter.data.ruins import RUIN_TYPES, can_clear

    slot = state.get_room_slot(state.popup_floor, state.popup_room)
    ruin_key = slot.get("ruin_type", "debris_back")
    ruin = RUIN_TYPES.get(ruin_key, RUIN_TYPES["debris_back"])
    can, reasons = can_clear(state, ruin)

    font = fonts["small"]
    rect = _popup_rect()
    body = _body_rect(rect)
    desc_lines = _wrap_text(ruin["description"], font, body.width - 20)

    conditions = ruin.get("conditions", [])
    rows = (
        desc_lines
        + ["cost"]
        + (["条件"] if conditions else [])
        + [f"cond:{c}" for c in conditions]
        + [f"fail:{r}" for r in reasons]
        + ["button"]
    )
    content_h = TITLE_BAR_HEIGHT + BODY_TOP_PAD + len(rows) * POPUP_ROW_HEIGHT + 16
    state.popup_content_height = content_h

    _draw_popup_frame(surface, rect)
    _draw_title(surface, rect, ruin["name"], font)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    start_y = _content_start_y(rect) - state.popup_scroll_offset

    _start_scroll(surface, rect, state, content_h)
    row = 0

    # description
    for line in desc_lines:
        _text_row(surface, rect, start_y, row, line, font, COLOR_TEXT_DIM)
        row += 1

    # cost
    cost_str = room_system.cost_cn(ruin["clear_cost"])
    _text_row(surface, rect, start_y, row,
              f"清理成本: {cost_str}   耗时: {ruin['clear_time']}s",
              font, COLOR_TEXT_BRIGHT)
    row += 1

    # separator
    _draw_hline(surface, start_y + row * POPUP_ROW_HEIGHT - 4, rect.x + 12, rect.right - 12)

    # conditions
    if conditions:
        _text_row(surface, rect, start_y, row, "条件:", font, COLOR_TEXT_MID)
        row += 1
        for cond in conditions:
            label = _condition_label(cond)
            status = "[满足]" if can else "[未满足]"
            status_color = COLOR_TEXT_BRIGHT if can else (120, 60, 60)
            _text_row(surface, rect, start_y, row,
                      f"  {status}  {label}", font, status_color)
            row += 1

    if not can and reasons:
        for reason in reasons:
            _text_row(surface, rect, start_y, row,
                      f"  -> {reason}", font, COLOR_TEXT_DIM)
            row += 1

    # clear button
    btn_label = "[ 开始清理 ]" if can else "[ 条件不足 ]"
    btn_color = COLOR_TEXT_BRIGHT if can else COLOR_TEXT_DIM
    btn_y = start_y + row * POPUP_ROW_HEIGHT
    btn_rect = pygame.Rect(rect.x + 12, btn_y, rect.width - 24, POPUP_ROW_HEIGHT)
    global _last_button_rect
    _last_button_rect = btn_rect.copy()
    btn_hover = can and btn_rect.collidepoint(mouse_x, mouse_y)
    if btn_hover:
        pygame.draw.rect(surface, POPUP_ROW_HOVER, btn_rect, border_radius=2)
    btn_surf = font.render(btn_label, True, btn_color)
    surface.blit(btn_surf, (btn_rect.x + 8, btn_rect.y + 6))

    _end_scroll(surface)


def handle_ruin_info_click(pos: tuple, state) -> bool:
    """Handle click inside the ruin info popup."""
    from shelter.data.ruins import RUIN_TYPES, can_clear

    slot = state.get_room_slot(state.popup_floor, state.popup_room)
    ruin_key = slot.get("ruin_type", "debris_back")
    ruin = RUIN_TYPES.get(ruin_key, RUIN_TYPES["debris_back"])
    can, reasons = can_clear(state, ruin)

    rect = _popup_rect()
    x, y = pos

    if not rect.collidepoint(x, y):
        state.close_popup()
        return False

    if not can:
        state.close_popup()
        return True

    global _last_button_rect
    if _last_button_rect and _last_button_rect.collidepoint(x, y):
        cost = ruin["clear_cost"]
        can_afford, failures = room_system.check_resources(state, cost)
        if not can_afford:
            for msg in failures:
                state.add_log(msg)
            state.close_popup()
            return True
        room_system.deduct_resources(state, cost)
        room_system.start_clearing(state, state.popup_floor, state.popup_room, ruin["clear_time"])
        state.add_log(f"开始清理 {ruin['name']}，预计 {ruin['clear_time']} 秒后完成。")
        state.close_popup()
        return True

    state.close_popup()
    return False


# ============================================================
# Room info popup (left-click built slot)
# ============================================================

def draw_room_info(surface: pygame.Surface, state, fonts: dict):
    """Draw room information popup."""
    from shelter.data.rooms import get_room
    from shelter.data.job_types import get_job

    slot = state.get_room_slot(state.popup_floor, state.popup_room)
    tmpl = get_room(slot.get("room_type", ""))
    if not tmpl:
        return

    font = fonts["small"]
    rect = _popup_rect()
    body = _body_rect(rect)
    desc_lines = _wrap_text(tmpl["description"], font, body.width - 20)

    # Compute content height dynamically based on the actual rows we will draw.
    n_rows = len(desc_lines) + 1  # desc + separator
    job_rows = 0
    if tmpl.get("job_type"):
        job_rows += 1  # job name + slots
        rate_text = ""
        prod_parts = [f"{room_system.res_cn(k)}+{v}/天/人" for k, v in tmpl.get("production_per_day", {}).items()]
        cons_parts = [f"{room_system.res_cn(k)}-{v}/天/人" for k, v in tmpl.get("consumption_per_day", {}).items()]
        rate_text = "  ".join(prod_parts + cons_parts)
        if rate_text:
            job_rows += 1
    elif tmpl.get("passive_consumption_per_day") or tmpl.get("passive_production_per_day"):
        parts = []
        for k, v in tmpl.get("passive_production_per_day", {}).items():
            parts.append(f"{room_system.res_cn(k)}+{v}/天")
        for k, v in tmpl.get("passive_consumption_per_day", {}).items():
            parts.append(f"{room_system.res_cn(k)}-{v}/天")
        if parts:
            job_rows += 1
    n_rows += job_rows + 1  # separator

    upg = tmpl.get("upgrades_to", [])
    upg_names = []
    for uk in upg:
        ut = get_room(uk)
        upg_names.append(ut["name"] if ut else uk)
    n_rows += 1  # upgrade
    if tmpl.get("downgrade_to"):
        n_rows += 1
    n_rows += 1  # separator + hint

    content_h = TITLE_BAR_HEIGHT + BODY_TOP_PAD + n_rows * POPUP_ROW_HEIGHT + 16
    state.popup_content_height = content_h

    _draw_popup_frame(surface, rect)
    _draw_title(surface, rect, f"{tmpl['name']}  Lv.{slot['level']}", font)

    start_y = _content_start_y(rect) - state.popup_scroll_offset

    _start_scroll(surface, rect, state, content_h)
    row = 0

    for line in desc_lines:
        _text_row(surface, rect, start_y, row, line, font, COLOR_TEXT_DIM)
        row += 1
    _draw_hline(surface, start_y + row * POPUP_ROW_HEIGHT - 4, rect.x + 12, rect.right - 12)

    # job type info
    jt = get_job(tmpl.get("job_type", "")) if tmpl.get("job_type") else None
    if jt:
        job_name = jt["name"]
        job_slots = tmpl.get("job_slots", 0)
        current = state.job_assignment.get(tmpl["job_type"], 0)
        _text_row(surface, rect, start_y, row,
                  f"岗位: {job_name}  {current}/{job_slots}", font, COLOR_TEXT_BRIGHT)
        row += 1

        prod_parts = [f"{room_system.res_cn(k)}+{v}/天/人" for k, v in tmpl.get("production_per_day", {}).items()]
        cons_parts = [f"{room_system.res_cn(k)}-{v}/天/人" for k, v in tmpl.get("consumption_per_day", {}).items()]
        rate_text = "  ".join(prod_parts + cons_parts)
        if rate_text:
            _text_row(surface, rect, start_y, row, rate_text, font, COLOR_TEXT_MID)
            row += 1
    elif tmpl.get("passive_consumption_per_day") or tmpl.get("passive_production_per_day"):
        parts = []
        for k, v in tmpl.get("passive_production_per_day", {}).items():
            parts.append(f"{room_system.res_cn(k)}+{v}/天")
        for k, v in tmpl.get("passive_consumption_per_day", {}).items():
            parts.append(f"{room_system.res_cn(k)}-{v}/天")
        if parts:
            _text_row(surface, rect, start_y, row,
                      f"被动: {'  '.join(parts)}", font, COLOR_TEXT_MID)
            row += 1

    _draw_hline(surface, start_y + row * POPUP_ROW_HEIGHT - 4, rect.x + 12, rect.right - 12)

    # upgrade info
    _text_row(surface, rect, start_y, row,
              f"可升级: {', '.join(upg_names) if upg_names else '无'}",
              font, COLOR_TEXT_MID)
    row += 1

    if tmpl.get("downgrade_to"):
        dt = get_room(tmpl["downgrade_to"])
        if dt:
            _text_row(surface, rect, start_y, row,
                      f"可降级: {dt['name']}", font, COLOR_TEXT_MID)
            row += 1

    _draw_hline(surface, start_y + row * POPUP_ROW_HEIGHT - 4, rect.x + 12, rect.right - 12)
    _text_row(surface, rect, start_y, row, "[ 右键点击房间进行升级/降级/拆除 ]",
              font, COLOR_TEXT_DIM)

    _end_scroll(surface)


def handle_room_info_click(pos: tuple, state) -> bool:
    state.close_popup()
    return True


# ============================================================
# Room action popup (right-click built slot)
# ============================================================

# each action = 2 rows (title + subtitle)
ACTION_ENTRY_H = POPUP_ROW_HEIGHT * 2 + POPUP_CARD_GAP


def draw_room_action(surface: pygame.Surface, state, fonts: dict):
    """Draw right-click action menu for a built room."""
    slot = state.get_room_slot(state.popup_floor, state.popup_room)
    from shelter.data.rooms import get_room
    tmpl = get_room(slot.get("room_type", ""))
    if not tmpl:
        return

    actions = room_system.get_upgrade_options(state, state.popup_floor, state.popup_room)
    n = len(actions)
    content_h = TITLE_BAR_HEIGHT + BODY_TOP_PAD + n * ACTION_ENTRY_H + 12
    state.popup_content_height = content_h
    rect = _popup_rect()

    _draw_popup_frame(surface, rect)
    font = fonts["small"]
    _draw_title(surface, rect, f"{tmpl['name']}  Lv.{slot['level']} — 操作", font)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    start_y = _content_start_y(rect) - state.popup_scroll_offset

    _start_scroll(surface, rect, state, content_h)

    for i, action in enumerate(actions):
        entry_top = start_y + i * ACTION_ENTRY_H

        # title row
        title_rect = pygame.Rect(rect.x + 8, entry_top, rect.width - 16, POPUP_ROW_HEIGHT)
        hover = title_rect.collidepoint(mouse_x, mouse_y)
        if hover:
            pygame.draw.rect(surface, POPUP_ROW_HOVER, title_rect, border_radius=2)

        title_color = COLOR_TEXT_BRIGHT
        if action["action_type"] == "demolish":
            title_color = (200, 100, 100)  # dim red for demolish
        title_surf = font.render(action["label"], True, title_color)
        surface.blit(title_surf, (title_rect.x + 4, title_rect.y + 6))

        # subtext row
        sub_y = entry_top + POPUP_ROW_HEIGHT
        sub_surf = font.render(action["subtext"], True, COLOR_TEXT_DIM)
        surface.blit(sub_surf, (rect.x + 16, sub_y + 6))

        if i < n - 1:
            sep_y = entry_top + ACTION_ENTRY_H - 1
            _draw_hline(surface, sep_y, rect.x + 12, rect.right - 12)

    _end_scroll(surface)


def handle_room_action_click(pos: tuple, state) -> bool:
    """Handle click inside the room action popup."""
    slot = state.get_room_slot(state.popup_floor, state.popup_room)
    from shelter.data.rooms import get_room
    tmpl = get_room(slot.get("room_type", ""))
    if not tmpl:
        state.close_popup()
        return False

    actions = room_system.get_upgrade_options(state, state.popup_floor, state.popup_room)
    n = len(actions)
    rect = _popup_rect()
    x, y = pos

    if not rect.collidepoint(x, y):
        state.close_popup()
        return False

    start_y = _content_start_y(rect) - state.popup_scroll_offset

    for i, action in enumerate(actions):
        entry_top = start_y + i * ACTION_ENTRY_H
        title_rect = pygame.Rect(rect.x + 8, entry_top, rect.width - 16, POPUP_ROW_HEIGHT)
        if title_rect.collidepoint(x, y):
            room_system.apply_room_action(
                state, state.popup_floor, state.popup_room,
                action["action_type"], action["target_key"]
            )
            state.close_popup()
            return True

    state.close_popup()
    return False


# ============================================================
# Story popup (intro-driven info / choice panel)
# ============================================================

TUTORIAL_LINE_HEIGHT = 22
CHOICE_LINE_HEIGHT = 26


def _story_popup_layout(state):
    """Compute story popup geometry shared by draw and click handlers.
    Returns (mode, title, lines, choices, rect, start_y, choice_y).
    """
    mode = getattr(state, "story_popup_mode", "info")
    title = getattr(state, "story_popup_title", "")
    text = getattr(state, "story_popup_text", "")
    lines = text.split("\n") if text else []
    choices = getattr(state, "story_choices", []) or [] if mode == "choice" else []
    if mode == "choice":
        content_h = TITLE_BAR_HEIGHT + 16 + len(lines) * TUTORIAL_LINE_HEIGHT + 16 + len(choices) * CHOICE_LINE_HEIGHT + 42
    else:
        content_h = TITLE_BAR_HEIGHT + 16 + len(lines) * TUTORIAL_LINE_HEIGHT + 42
    state.popup_content_height = content_h
    rect = _popup_rect()
    start_y = _content_start_y(rect) - state.popup_scroll_offset
    choice_y = start_y + len(lines) * TUTORIAL_LINE_HEIGHT + 16 if mode == "choice" else None
    return mode, title, lines, choices, rect, start_y, choice_y


def draw_story(surface: pygame.Surface, state, fonts: dict):
    """Draw a story popup: either info text or a list of choices."""
    mode, title, lines, choices, rect, start_y, choice_y = _story_popup_layout(state)

    _draw_popup_frame(surface, rect)
    font = fonts["small"]
    _draw_title(surface, rect, title, font)

    _start_scroll(surface, rect, state, state.popup_content_height)

    for i, line in enumerate(lines):
        surf = font.render(line, True, COLOR_TEXT_BRIGHT)
        surface.blit(surf, (rect.x + 16, start_y + i * TUTORIAL_LINE_HEIGHT))

    if mode == "choice":
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i, choice in enumerate(choices):
            row_y = choice_y + i * CHOICE_LINE_HEIGHT
            row_rect = pygame.Rect(rect.x + 16, row_y, rect.width - 32, CHOICE_LINE_HEIGHT - 4)
            hover = row_rect.collidepoint(mouse_x, mouse_y)
            bg = POPUP_ROW_HOVER if hover else (30, 30, 30)
            pygame.draw.rect(surface, bg, row_rect, border_radius=2)
            pygame.draw.rect(surface, COLOR_BORDER, row_rect, width=1, border_radius=2)
            text_surf = font.render(f"{i + 1}. {choice.get('text', '')}", True, COLOR_TEXT_BRIGHT)
            surface.blit(text_surf, (row_rect.x + 8, row_rect.y + 4))

    _end_scroll(surface)

    if mode != "choice":
        # close hint (outside scrollable body)
        hint = font.render("[ 点击任意处或按 Esc 关闭 ]", True, COLOR_TEXT_DIM)
        hint_y = rect.bottom - 30
        surface.blit(hint, (rect.centerx - hint.get_width() // 2, hint_y))


def handle_story_click(pos: tuple, state) -> bool:
    """Handle click inside a story popup. Info mode closes; choice mode selects.

    Note: closing an info popup does NOT resume the story. The story only resumes
    when the player clicks the tab designated by `state.story_resume_tab`.
    """
    from shelter.systems import story_system

    mode, _title, lines, choices, rect, start_y, choice_y = _story_popup_layout(state)
    x, y = pos

    if mode == "choice":
        if not rect.collidepoint(x, y):
            return False
        for i, _choice in enumerate(choices):
            row_y = choice_y + i * CHOICE_LINE_HEIGHT
            row_rect = pygame.Rect(rect.x + 16, row_y, rect.width - 32, CHOICE_LINE_HEIGHT - 4)
            if row_rect.collidepoint(x, y):
                story_system.choose(state, i)
                return True
        return False

    # Info mode: close only. The outer loop will resume when the player returns
    # to the resume tab (usually TAB_STATUS).
    state.close_popup()
    return True


def handle_tutorial_click(pos: tuple, state) -> bool:
    """Deprecated alias; kept for compatibility."""
    return handle_story_click(pos, state)


def draw_tutorial(surface: pygame.Surface, state, fonts: dict):
    """Deprecated alias; kept for compatibility."""
    return draw_story(surface, state, fonts)


def _text_row(surface: pygame.Surface, rect: pygame.Rect, start_y: int,
              row_idx: int, text: str, font, color=None):
    """Draw a single line of text within the popup body. No hover, no border."""
    y = start_y + row_idx * POPUP_ROW_HEIGHT
    c = color or COLOR_TEXT_BRIGHT
    surf = font.render(text, True, c)
    surface.blit(surf, (rect.x + 14, y + 6))


def _condition_label(cond: dict) -> str:
    ctype = cond.get("type", "")
    if ctype == "has_resources":
        parts = [f"{room_system.res_cn(k)}:{v}" for k, v in cond.items() if k != "type"]
        return f"拥有资源: {' '.join(parts)}"
    elif ctype == "has_room":
        from shelter.data.rooms import get_room
        rk = cond.get("room_type", "?")
        tmpl = get_room(rk)
        name = tmpl["name"] if tmpl else rk
        return f"已建造: {name}"
    elif ctype == "stat_check":
        parts = []
        if "min_total_power" in cond:
            parts.append(f"总电力 >= {cond['min_total_power']}")
        if "min_total_water" in cond:
            parts.append(f"总水 >= {cond['min_total_water']}")
        return "  ".join(parts)
    elif ctype == "min_population":
        return f"人口 >= {cond.get('value', 0)}"
    return str(cond)


# ============================================================
# Shared wheel handler
# ============================================================

POPUP_WHEEL_STEP = 30


def handle_wheel(y_offset: int, state) -> bool:
    """Scroll the currently open popup. Returns True if the event was consumed."""
    if not state.popup_type:
        return False
    state.popup_scroll_offset -= y_offset * POPUP_WHEEL_STEP
    # Clamp happens during the next draw.
    return True
