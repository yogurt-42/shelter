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
    return [
        "--- Admin Commands ---",
        "//help              Show all commands",
        "//clear             Clear the log",
        "//hide <tab>        Hide a tab (e.g. //hide build)",
        "//show <tab>        Show a tab (e.g. //show build)",
        "//tabs              List visible tabs",
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
