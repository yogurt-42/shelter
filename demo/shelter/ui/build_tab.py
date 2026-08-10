"""Shelter UI — build tab (pannable 5-floor map with room grid + surface separator)."""

import time
import pygame
from shelter.config import (
    WINDOW_WIDTH,
    MAIN_AREA_Y,
    MAIN_AREA_HEIGHT,
    FLOORS,
    ROOMS_PER_FLOOR,
    ROOM_CELL_WIDTH,
    ROOM_CELL_HEIGHT,
    ROOM_CELL_PADDING,
    MAP_LEFT_MARGIN,
    MAP_TOP_MARGIN,
    ROOM_STATE_EMPTY,
    ROOM_STATE_RUIN,
    ROOM_STATE_BUILT,
    ROOM_STATE_BUILDING,
    ROOM_STATE_CLEARING,
    BUILD_DRAG_LIMIT_Y,
    BUILD_DRAG_LIMIT_X,
    MINI_LOG_HEIGHT,
    COLOR_BG,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MID,
    COLOR_BORDER,
    COLOR_BORDER_LIGHT,
    COLOR_CELL_EMPTY_BG,
    COLOR_CELL_RUIN_BG,
    COLOR_CELL_BUILT_BG,
    COLOR_CELL_HOVER_BORDER,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
)

STATE_LABELS = {
    ROOM_STATE_EMPTY: "空置",
    ROOM_STATE_RUIN: "废墟",
    ROOM_STATE_BUILT: "已建造",
    ROOM_STATE_BUILDING: "建造中",
    ROOM_STATE_CLEARING: "清理中",
}

# ---- drag state (module-level, UI-only) ----
_dragging = False
_drag_start_mouse_x = 0
_drag_start_mouse_y = 0
_drag_start_offset_x = 0.0
_drag_start_offset_y = 0.0
_drag_moved = False

DRAG_THRESHOLD = 5


def _content_rect() -> pygame.Rect:
    """Content area of the build tab (main area minus mini-log)."""
    return pygame.Rect(0, MAIN_AREA_Y, WINDOW_WIDTH, MAIN_AREA_HEIGHT - MINI_LOG_HEIGHT)


def _floor_header_height() -> int:
    return 22


def _floor_row_height() -> int:
    return ROOM_CELL_HEIGHT + ROOM_CELL_PADDING * 2


def _floor_total_height() -> int:
    return _floor_header_height() + _floor_row_height() + 4


def _get_ruin_name(ruin_key: str) -> str:
    """Return a short Chinese display name for a ruin key."""
    from shelter.data.ruins import RUIN_TYPES
    ruin = RUIN_TYPES.get(ruin_key)
    return ruin["name"] if ruin else "废墟"


def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the build tab map with clipping, bi-directional pan, and surface separator."""
    content_rect = _content_rect()
    content_top = content_rect.top

    pygame.draw.rect(surface, COLOR_BG, content_rect)

    # ---- clip so content never bleeds into adjacent UI ----
    surface.set_clip(content_rect)

    font = fonts["small"]
    offset_x = state.build_view_offset_x
    offset_y = state.build_view_offset_y

    fhh = _floor_header_height()
    fth = _floor_total_height()
    mouse_x, mouse_y = pygame.mouse.get_pos()

    now = time.time()

    for f in range(FLOORS):
        base_y = content_top + MAP_TOP_MARGIN + f * fth + offset_y

        # skip floors entirely outside the visible area
        if base_y + fth < content_top:
            continue
        if base_y > content_top + content_rect.height:
            continue

        # ---- floor label ----
        label = f"第{f + 1}层"
        title_surf = font.render(label, True, COLOR_TEXT_BRIGHT)
        surface.blit(title_surf, (MAP_LEFT_MARGIN + offset_x, base_y))

        # ---- room cells ----
        cell_y = base_y + fhh + 2

        for r in range(ROOMS_PER_FLOOR):
            cell_x = MAP_LEFT_MARGIN + r * (ROOM_CELL_WIDTH + ROOM_CELL_PADDING) + offset_x
            cell_rect = pygame.Rect(cell_x, cell_y, ROOM_CELL_WIDTH, ROOM_CELL_HEIGHT)

            room = state.floors[f][r]
            room_state = room["state"]

            if room_state == ROOM_STATE_EMPTY:
                bg = COLOR_CELL_EMPTY_BG
            elif room_state == ROOM_STATE_RUIN:
                bg = COLOR_CELL_RUIN_BG
            elif room_state == ROOM_STATE_BUILDING:
                bg = (55, 55, 35)  # slightly warm tint
            elif room_state == ROOM_STATE_CLEARING:
                bg = (55, 45, 35)  # slightly warm tint
            else:
                bg = COLOR_CELL_BUILT_BG

            pygame.draw.rect(surface, bg, cell_rect)

            # border / hover highlight
            is_hover = cell_rect.collidepoint(mouse_x, mouse_y)
            border_color = COLOR_CELL_HOVER_BORDER if is_hover else COLOR_BORDER
            pygame.draw.rect(surface, border_color, cell_rect, width=1)

            # ---- cell label ----
            if room_state == ROOM_STATE_BUILT and room["room_type"]:
                from shelter.data.rooms import get_room
                tmpl = get_room(room["room_type"])
                room_name = tmpl["name"] if tmpl else room["room_type"]
                label_text = f"{room_name} Lv.{room['level']}"
            elif room_state == ROOM_STATE_RUIN and room.get("ruin_type"):
                label_text = _get_ruin_name(room["ruin_type"])
            elif room_state in (ROOM_STATE_BUILDING, ROOM_STATE_CLEARING):
                label_text = STATE_LABELS[room_state]
            else:
                label_text = STATE_LABELS.get(room_state, "?")

            cell_label = font.render(label_text, True, COLOR_TEXT_MID)
            lx = cell_x + (ROOM_CELL_WIDTH - cell_label.get_width()) // 2
            ly = cell_y + (ROOM_CELL_HEIGHT - cell_label.get_height()) // 2 - 4
            surface.blit(cell_label, (lx, ly))

            # ---- progress bar for building/clearing ----
            if room_state in (ROOM_STATE_BUILDING, ROOM_STATE_CLEARING) and room.get("build_end_time"):
                remaining = max(0, room["build_end_time"] - now)
                # Infer total duration from room data
                if room_state == ROOM_STATE_BUILDING:
                    total = _get_build_time(room["room_type"])
                else:
                    total = _get_clear_time(room.get("ruin_type", "light_rubble"))

                if total > 0:
                    elapsed = total - remaining
                    progress = min(1.0, max(0.0, elapsed / total))

                    bar_y = cell_y + ROOM_CELL_HEIGHT - 8
                    bar_h = 4
                    bar_w = ROOM_CELL_WIDTH - 8

                    # background
                    bar_bg_rect = pygame.Rect(cell_x + 4, bar_y, bar_w, bar_h)
                    pygame.draw.rect(surface, (40, 40, 40), bar_bg_rect)
                    # fill
                    filled = int(bar_w * progress)
                    if filled > 0:
                        fill_color = (140, 140, 60) if room_state == ROOM_STATE_BUILDING else (140, 100, 60)
                        fill_rect = pygame.Rect(cell_x + 4, bar_y, filled, bar_h)
                        pygame.draw.rect(surface, fill_color, fill_rect)

                    # time remaining hint
                    secs_left = int(remaining)
                    hint = font.render(f"{secs_left}s", True, COLOR_TEXT_DIM)
                    hint_x = cell_x + ROOM_CELL_WIDTH - hint.get_width() - 4
                    hint_y = bar_y - hint.get_height() - 1
                    surface.blit(hint, (hint_x, hint_y))

        # ---- surface separator (between floor 1 and floor 2) ----
        if f == 0:
            sep_y = base_y + fth + 2
            sep_rect = pygame.Rect(
                MAP_LEFT_MARGIN + offset_x,
                sep_y,
                ROOMS_PER_FLOOR * (ROOM_CELL_WIDTH + ROOM_CELL_PADDING) - ROOM_CELL_PADDING,
                8,
            )
            pygame.draw.rect(surface, (25, 25, 25), sep_rect)
            # dashed line
            dash_width = 20
            gap = 12
            total_width = sep_rect.width
            dx = sep_rect.x
            while dx < sep_rect.x + total_width:
                dash_rect = pygame.Rect(dx, sep_y + 3, dash_width, 2)
                pygame.draw.rect(surface, COLOR_BORDER, dash_rect)
                dx += dash_width + gap

    # ---- restore clip ----
    surface.set_clip(None)


def _get_build_time(room_type: str | None) -> float:
    if not room_type:
        return 1
    from shelter.data.rooms import get_room
    tmpl = get_room(room_type)
    return tmpl["build_time"] if tmpl else 1


def _get_clear_time(ruin_type: str) -> float:
    from shelter.data.ruins import RUIN_TYPES
    ruin = RUIN_TYPES.get(ruin_type)
    return ruin["clear_time"] if ruin else 10


# ============================================================
# Drag handlers
# ============================================================

def handle_mouse_down(pos: tuple, state) -> bool:
    global _dragging, _drag_start_mouse_x, _drag_start_mouse_y
    global _drag_start_offset_x, _drag_start_offset_y, _drag_moved

    x, y = pos
    content_rect = _content_rect()
    if not content_rect.collidepoint(x, y):
        return False

    _dragging = True
    _drag_start_mouse_x = x
    _drag_start_mouse_y = y
    _drag_start_offset_x = state.build_view_offset_x
    _drag_start_offset_y = state.build_view_offset_y
    _drag_moved = False
    return True


def handle_mouse_motion(pos: tuple, state) -> bool:
    global _dragging, _drag_moved
    if not _dragging:
        return False

    x, y = pos
    dx = x - _drag_start_mouse_x
    dy = y - _drag_start_mouse_y

    if abs(dx) >= DRAG_THRESHOLD or abs(dy) >= DRAG_THRESHOLD:
        _drag_moved = True

    # vertical: clamped to ±BUILD_DRAG_LIMIT_Y
    new_oy = _drag_start_offset_y + dy
    new_oy = max(-BUILD_DRAG_LIMIT_Y, min(BUILD_DRAG_LIMIT_Y, new_oy))
    state.build_view_offset_y = new_oy

    # horizontal: grab-and-pull. drag left → offset decreases → right rooms revealed.
    new_ox = _drag_start_offset_x + dx
    new_ox = max(-BUILD_DRAG_LIMIT_X, min(0, new_ox))
    state.build_view_offset_x = new_ox

    return True


def handle_mouse_up(pos: tuple, state) -> bool:
    global _dragging, _drag_moved
    if not _dragging:
        return False

    _dragging = False

    if not _drag_moved:
        return _handle_room_click(pos, state, button=1)

    return True


# ============================================================
# Click handling
# ============================================================

def _find_room_at(pos: tuple, state) -> tuple | None:
    """Find which (floor, room, cell_rect, slot) is under the mouse."""
    x, y = pos
    content_rect = _content_rect()
    if not content_rect.collidepoint(x, y):
        return None

    offset_x = state.build_view_offset_x
    offset_y = state.build_view_offset_y
    fhh = _floor_header_height()
    fth = _floor_total_height()

    for f in range(FLOORS):
        base_y = content_rect.top + MAP_TOP_MARGIN + f * fth + offset_y
        cell_y = base_y + fhh + 2

        for r in range(ROOMS_PER_FLOOR):
            cell_x = MAP_LEFT_MARGIN + r * (ROOM_CELL_WIDTH + ROOM_CELL_PADDING) + offset_x
            cell_rect = pygame.Rect(cell_x, cell_y, ROOM_CELL_WIDTH, ROOM_CELL_HEIGHT)
            if cell_rect.collidepoint(x, y):
                return (f, r, cell_rect, state.floors[f][r])

    return None


def _handle_room_click(pos: tuple, state, button: int = 1) -> bool:
    """Handle a click on the build map. Opens the appropriate popup."""
    hit = _find_room_at(pos, state)
    if hit is None:
        return False

    f, r, cell_rect, slot = hit
    room_state = slot["state"]

    if button == 1:  # left click
        if room_state == ROOM_STATE_EMPTY:
            state.open_popup("build", f, r)
        elif room_state == ROOM_STATE_RUIN:
            state.open_popup("ruin_info", f, r)
        elif room_state == ROOM_STATE_BUILT:
            state.open_popup("room_info", f, r)
        elif room_state == ROOM_STATE_BUILDING:
            state.open_popup("room_info", f, r)
        elif room_state == ROOM_STATE_CLEARING:
            state.open_popup("ruin_info", f, r)
        return True

    elif button == 3:  # right click
        if room_state == ROOM_STATE_BUILT:
            state.open_popup("room_action", f, r)
            return True

    return False


def handle_right_click(pos: tuple, state) -> bool:
    """Handle right-click on the build tab map."""
    return _handle_room_click(pos, state, button=3)
