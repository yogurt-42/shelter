"""Shelter UI — bottom command console. Supports /player and //admin commands."""

import pygame
from shelter.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    CONSOLE_HEIGHT,
    TAB_STATUS,
    TAB_BUILD,
    TAB_POPULATION,
    COLOR_CONSOLE_BG,
    COLOR_CONSOLE_PROMPT,
    COLOR_CONSOLE_TEXT,
    COLOR_CONSOLE_CURSOR,
    COLOR_BORDER,
    FONT_SIZE_NORMAL,
)

CURSOR_BLINK_MS = 530

# tab name -> key mapping
TAB_NAME_MAP = {"status": TAB_STATUS, "build": TAB_BUILD, "population": TAB_POPULATION}
TAB_KEY_NAME = {TAB_STATUS: "status", TAB_BUILD: "build", TAB_POPULATION: "population"}


# ---- command handlers ----

def _cmd_help(state) -> list[str]:
    return [
        "--- Available Commands ---",
        "/help    Show this help",
        "/status  Show resource summary",
        "--- Tip ---",
        'Commands starting with "//" are admin commands. Type //help for more.',
    ]


def _cmd_admin_help(state) -> list[str]:
    mode_flags = []
    if state.infinite_resources:
        mode_flags.append("无限资源")
    if state.full_speed:
        mode_flags.append("极速建造")
    mode_status = "、".join(mode_flags) if mode_flags else "无"
    return [
        "--- Admin Commands ---",
        "//help              Show all commands",
        "//clear             Clear the log",
        "//hide <tab>        Hide a tab (e.g. //hide build)",
        "//show <tab>        Show a tab (e.g. //show build)",
        "//tabs              List visible tabs",
        "//i am infinite     无限资源 — 无视资源消耗与上限",
        "//full speed        极速建造 — 所有等待时间归零",
        "//it is enough      退出所有管理员状态",
        "//i am 42           开启所有管理员状态",
        f"当前管理模式: {mode_status}",
    ]


def _cmd_status(state) -> list[str]:
    return [
        f"电力: {int(state.power)}/{int(state.max_power)}",
        f"水:   {int(state.water)}/{int(state.max_water)}",
        f"食物: {int(state.food)}/{int(state.max_food)}",
        f"废料: {int(state.scrap)}",
        f"运行时间: {state.elapsed_days}天{state.elapsed_hours}时{state.elapsed_minutes}分",
    ]


def _cmd_clear(state) -> list[str]:
    state.logs.clear()
    state.log_scroll_offset = 0
    return ["Log cleared."]


def _cmd_hide(state, args: str) -> list[str]:
    name = args.strip()
    key = TAB_NAME_MAP.get(name)
    if key is None:
        return [f"Unknown tab: {name}, available: {', '.join(TAB_NAME_MAP.keys())}"]
    if key not in state.visible_tabs:
        return [f"Tab '{name}' is already hidden."]
    state.visible_tabs.discard(key)
    if state.active_tab == key:
        from shelter.ui.tab_bar import get_first_visible
        state.active_tab = get_first_visible(state)
    return [f"Tab '{name}' hidden."]


def _cmd_show(state, args: str) -> list[str]:
    name = args.strip()
    key = TAB_NAME_MAP.get(name)
    if key is None:
        return [f"Unknown tab: {name}, available: {', '.join(TAB_NAME_MAP.keys())}"]
    if key in state.visible_tabs:
        return [f"Tab '{name}' is already visible."]
    state.visible_tabs.add(key)
    return [f"Tab '{name}' shown."]


def _cmd_tabs(state) -> list[str]:
    names = [TAB_KEY_NAME[k] for k in sorted(state.visible_tabs)]
    return [f"Visible tabs: {', '.join(names) if names else '(none)'}"]


def _cmd_infinite(state) -> list[str]:
    state.infinite_resources = True
    return ["[管理模式] 无限资源已开启 — 无视所有资源消耗与上限。"]


def _cmd_full_speed(state) -> list[str]:
    state.full_speed = True
    # fast-forward all in-progress constructions
    count = 0
    for floor in state.floors:
        for slot in floor:
            if slot.get("action_type") and slot.get("build_end_time") is not None:
                slot["build_end_time"] = 0
                count += 1
    return [f"[管理模式] 极速建造已开启 — 所有等待时间归零，{count} 个在建项目即刻完成。"]


def _cmd_enough(state) -> list[str]:
    state.infinite_resources = False
    state.full_speed = False
    return ["[管理模式] 已退出所有管理员状态。"]


def _cmd_i_am_42(state) -> list[str]:
    state.infinite_resources = True
    state.full_speed = True
    # fast-forward all in-progress constructions
    count = 0
    for floor in state.floors:
        for slot in floor:
            if slot.get("action_type") and slot.get("build_end_time") is not None:
                slot["build_end_time"] = 0
                count += 1
    return ["[管理模式] 已开启全部管理员状态：无限资源 + 极速建造。",
            f"{count} 个在建项目即刻完成。"]


# player command table
PLAYER_COMMANDS = {
    "help": _cmd_help,
    "status": _cmd_status,
}

# admin command table
ADMIN_COMMANDS = {
    "help": (lambda s, a: _cmd_admin_help(s), False),
    "clear": (lambda s, a: _cmd_clear(s), False),
    "hide": (lambda s, a: _cmd_hide(s, a), True),
    "show": (lambda s, a: _cmd_show(s, a), True),
    "tabs": (lambda s, a: _cmd_tabs(s), False),
}


def _execute(text: str, state) -> list[str]:
    """Parse and execute a command, returning output lines."""
    if text.startswith("//"):
        rest = text[2:].strip()
        rest_lower = rest.lower()

        # multi-word admin commands
        if rest_lower == "i am infinite":
            return _cmd_infinite(state)
        if rest_lower == "full speed":
            return _cmd_full_speed(state)
        if rest_lower == "it is enough":
            return _cmd_enough(state)
        if rest_lower == "i am 42":
            return _cmd_i_am_42(state)

        # single-word admin commands
        parts = rest.split(None, 1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        entry = ADMIN_COMMANDS.get(cmd)
        if entry is None:
            return [f"Unknown admin command: //{cmd}. Type //help for available commands."]
        handler, _has_args = entry
        return handler(state, args)

    elif text.startswith("/"):
        rest = text[1:].strip()
        parts = rest.split(None, 1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        handler = PLAYER_COMMANDS.get(cmd)
        if handler is None:
            return [f"Unknown command: /{cmd}. Type /help for available commands."]
        return handler(state)

    else:
        return [f"Unrecognized input: {text}. Commands start with / or //."]


# ---- draw ----

def draw(surface: pygame.Surface, state, fonts: dict):
    """Draw the bottom command console."""
    y = WINDOW_HEIGHT - CONSOLE_HEIGHT
    bar_rect = pygame.Rect(0, y, WINDOW_WIDTH, CONSOLE_HEIGHT)
    pygame.draw.rect(surface, COLOR_CONSOLE_BG, bar_rect)

    pygame.draw.line(surface, COLOR_BORDER, (0, y), (WINDOW_WIDTH, y))

    font = fonts["normal"]

    prompt = "> "
    prompt_surf = font.render(prompt, True, COLOR_CONSOLE_PROMPT)
    surface.blit(prompt_surf, (8, y + 5))

    input_x = 8 + prompt_surf.get_width()
    input_text = state.console_input
    if input_text:
        input_surf = font.render(input_text, True, COLOR_CONSOLE_TEXT)
        surface.blit(input_surf, (input_x, y + 5))
        cursor_x = input_x + input_surf.get_width()
    else:
        cursor_x = input_x

    now_ms = pygame.time.get_ticks()
    if (now_ms % (CURSOR_BLINK_MS * 2)) < CURSOR_BLINK_MS:
        cursor_surf = font.render("_", True, COLOR_CONSOLE_CURSOR)
        surface.blit(cursor_surf, (cursor_x, y + 5))


# ---- keyboard ----

def handle_key(event: pygame.event.Event, state) -> bool:
    if event.type != pygame.KEYDOWN:
        return False

    if event.key == pygame.K_BACKSPACE:
        state.console_input = state.console_input[:-1]
        return True

    if event.key == pygame.K_RETURN:
        text = state.console_input.strip()
        if text:
            state.add_log(f"> {text}")
            state.console_history.append(text)
            lines = _execute(text, state)
            for line in lines:
                state.add_log(line)
        state.console_input = ""
        return True

    if event.key == pygame.K_ESCAPE:
        state.console_input = ""
        return True

    if event.unicode and event.unicode.isprintable():
        state.console_input += event.unicode
        return True

    return False
