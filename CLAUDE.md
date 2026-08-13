# CLAUDE.md — AI Developer Onboarding

Project: **Shelter** — post-apocalyptic underground shelter management text game.
Single-developer Python + Pygame desktop app. Terminal aesthetic, monochrome palette,
Chinese player-facing text, English codebase.

## Quickstart

```bash
cd D:/shelter && python -m shelter.main          # launch game
cd D:/shelter && python -c "from shelter.game_state import GameState; ..."  # REPL testing
```

## Tech

- Python 3.12, Pygame 2.6, stdlib dataclasses
- No external deps beyond Pygame
- Font: SimHei (CJK) with Consolas fallback
- 1100×700 window, 30 FPS, single-threaded game loop

## Directory Map (~2800 LOC)

```
shelter/
├── main.py                     # entry: init pygame → event loop → tick → render
├── config.py                   # ALL constants (window, colors, fonts, layout, pacing)
├── game_state.py               # @dataclass GameState — single source of truth
├── save_system.py              # pickle-based save/load, 3 slots, saves/ folder
├── data/                       # static definitions (read-only at runtime)
│   ├── rooms.py                # ROOM_TEMPLATES dict, get_room(), list_buildable()
│   ├── ruins.py                # RUIN_TYPES, can_clear(), evaluate_condition()
│   ├── job_types.py            # JOB_DEFINITIONS, get_job()
│   ├── items.py                # ITEM_DEFINITIONS, get_item(), list_items()
│   └── events.py               # AMBIENT_EVENTS list (Chinese strings)
├── systems/                    # game logic, stateless, called per tick
│   ├── resource_system.py      # tick(state) → job production + passive drain + base scrap
│   ├── event_system.py         # tick(state) → random ambient log lines
│   └── room_system.py          # placeholder (unused)
└── ui/                         # rendering + input dispatch
    ├── renderer.py             # draw_all() — compositor, calls each module in order
    ├── tab_bar.py              # top tab strip, ALL_TABS registry, show/hide
    ├── resource_bar.py         # 4-resource row (power/water/food/scrap)
    ├── status_tab.py           # log viewer with scroll
    ├── build_tab.py            # 4-floor × 10-room pannable/zoomable map + drag + click routing
    ├── population_tab.py       # job-type aggregation, worker assignment
    ├── materials_tab.py        # resources + items inventory display
    ├── console.py              # bottom command line, /player //admin parsing
    └── popup.py                # overlay: build/ruin/room-info/room-action popups
```

## Core Architecture

### GameState (`game_state.py`)

`@dataclass` — THE single source of truth. Every module reads from this; only systems and
click handlers write to it. UI draw functions are pure: `draw(surface, state, fonts)`.

Key fields:

| Group | Fields |
|-------|--------|
| Tabs | `active_tab: int`, `visible_tabs: set[int]` |
| Resources | `power, water, food, scrap: float` + `max_power, max_water, max_food, max_scrap` |
| Items | `items: dict[str,int]` (item_key→count), `max_items: int` shared slot cap |
| Admin flags | `infinite_resources: bool`, `full_speed: bool` |
| Population | `population: int`, `job_assignment: dict[str,int]` (job_type→workers) |
| Floors | `floors: list[list[dict]]` — 4 floors × 10 rooms, each slot: `{state, room_type, level, ruin_type, build_end_time, action_type, revealed, void}` |
| UI state | `console_input`, `console_history`, `logs`, `log_scroll_offset`, `build_view_offset_x/y` |
| Popup | `popup_type: str\|None`, `popup_floor`, `popup_room` |
| Time | `elapsed_seconds`, `last_resource_tick`, `last_event_time` |

Key methods: `open_popup()`, `close_popup()`, `start_building()`, `start_clearing()`,
`complete_construction()`, `_propagate_vision()`, `_reveal_around()`, `_refresh_vision()`,
`free_workers`, `total_job_slots(job_type)`,
`assign_worker(job_type)`, `unassign_worker(job_type)`.

### Event Flow (main.py)

```
while running:
    for event in pygame.event.get():
        if QUIT: break
        if MOUSEBUTTONDOWN (btn 1):
            if popup open → popup handler
            elif tab_bar click → switch tab
            elif TAB_BUILD → build_tab drag start
            elif TAB_POPULATION → population_tab click
        if MOUSEBUTTONDOWN (btn 3):
            if TAB_BUILD → build_tab right-click
        if KEYDOWN:
            if ESC → close popup or clear console
            if TAB → cycle visible tabs
            else → console.handle_key()

    _tick_construction(state)         # check build/clear timers
    resource_system.tick(state)       # job production + passive drain + scrap
    event_system.tick(state)          # random ambient events

    renderer.draw_all(screen, state, fonts)
```

### Render Order (renderer.py)

```
1. TAB_BAR          (y=0, h=30)       always
2. RESOURCE_BAR     (y=30, h=28)      always
3. Active tab content (y=58..572)      one of: status / build(+mini-log) / population(+mini-log)
4. CONSOLE          (y=670, h=30)     always
5. Popup overlay    (centered)        if popup_type is set
```

### UI Module Interface

Every tab module exposes:
- `draw(surface, state, fonts)` — pure render
- `handle_click(pos, state) -> bool` or `handle_mouse_down/up/motion`
- Build tab additionally exposes `handle_wheel(y_offset, state) -> bool` for zoom
- Console: `handle_key(event, state) -> bool`
- Popup: `draw_xxx(surface, state, fonts)` + `handle_xxx_click(pos, state) -> bool`

### Room State Machine

```
EMPTY(0) ──[build click]──► BUILDING(3) ──[timer]──► BUILT(2)
RUIN(1) ──[clear click]──► CLEARING(4) ──[timer]──► EMPTY(0)
BUILT(2) ──[right-click]──► upgrade / downgrade / demolish
```

Some ruins define `clears_to: room_key` (e.g. `elevator_ruin` → `elevator`); when cleared
they become `BUILT` with that `room_type` instead of `EMPTY`.

Room slot dict: `{"state": int, "room_type": str|None, "level": int,
"ruin_type": str|None, "build_end_time": float|None, "action_type": str|None,
"revealed": bool, "void": bool}`

### Vision / Fog of War

- Each slot has `revealed` (player can see its real state) and `void` (no room at all).
- `EMPTY` and `BUILT` rooms reveal their left/right neighbors on the same floor.
- `elevator` rooms additionally reveal aligned elevator rooms directly above/below.
- Non-elevator rooms above/below an elevator are **not** revealed by that elevator.
- Clearing a ruin turns it into `EMPTY` (or a `BUILT` room via `clears_to`), which then
  expands vision. This is the primary way to explore deeper.
- `void` cells are never rendered or interactive.
- Unrevealed cells draw as an empty box with no state info and ignore clicks.

### Job/Population Model

- Rooms define `job_type` (str key into JOB_DEFINITIONS) + `job_slots` (int)
- Same-type room slots aggregate: 2 generators = 4 "power_tech" slots
- `state.job_assignment: {job_type: workers}` — assigned per type, NOT per room
- `state.free_workers = population - sum(job_assignment.values())`
- Resource production: `workers × per_worker_rate × dt` (from JOB_DEFINITIONS)
- Passive rooms (warehouse): `job_slots=0`, drain resources via `passive_consumption`

### Config Constants

```
TAB_STATUS=0, TAB_BUILD=1, TAB_POPULATION=2, TAB_MATERIALS=3
ROOM_STATE_EMPTY=0, RUIN=1, BUILT=2, BUILDING=3, CLEARING=4
FLOORS=4, ROOMS_PER_FLOOR=10
POPUP_WIDTH=520, POPUP_MAX_HEIGHT=560
BUILD_ZOOM_MIN=0.5, BUILD_ZOOM_MAX=2.0, BUILD_ZOOM_STEP=0.1
INITIAL_POPULATION=5, INITIAL_SCRAP=200, INITIAL_POWER=100
INITIAL_MAX_ITEMS=20
```

### Save System (`save_system.py`)

Pickle-based, 3 slots, saved to `saves/slot_N.sav` in project root.

| Function | Purpose |
|----------|---------|
| `save_game(state, slot)` | Pickle entire GameState + metadata → file |
| `load_game(slot)` | Read file → GameState (resets timers to now) |
| `list_saves()` | Scan all slots → metadata dicts (no unpickle) |
| `delete_save(slot)` | Remove one save file |

Commands (registered in `console.py` `_execute`):
- `/save [slot]` — default slot 1
- `/load [slot]` — replaces current state in-place via `__dict__` copy
- `/saves` — list all existing saves with game time, population, saved date

Startup: `main.py` checks for saves and adds a reminder log line if any exist.

## How to Add...

### A new tab
1. `config.py`: add `TAB_XXX = N`
2. `game_state.py`: add to `visible_tabs` default
3. `ui/tab_bar.py`: add `(TAB_XXX, "标签名")` to ALL_TABS
4. `ui/tab_xxx.py`: create module with `draw()` + `handle_click()`
5. `ui/renderer.py`: add `elif state.active_tab == TAB_XXX:` branch
6. `main.py`: add routing for mouse events
7. `ui/console.py`: add to TAB_NAME_MAP and TAB_KEY_NAME

### A new room type
1. `data/rooms.py`: add entry to ROOM_TEMPLATES with: key, name, description,
   build_cost, build_time, job_type (or None), job_slots (or 0),
   upgrades_to, downgrade_to, passive_consumption (optional)
2. If it has workers: add corresponding job type to `data/job_types.py`
3. Add to `list_buildable()` if it's a base (non-upgrade) room

### A new ruin type
1. `data/ruins.py`: add entry to RUIN_TYPES with: key, name, description,
   clear_cost, clear_time, conditions[], rewards[] (optional), clears_to (optional)
2. Add conditions using types: `has_resources`, `has_room`, `stat_check`
3. Assign to slots via `INITIAL_FLOOR_LAYOUT` in `data/ruins.py`

### Edit the map layout
1. Open `data/ruins.py` → `INITIAL_FLOOR_LAYOUT`
2. Each floor is a list of cell specs of length `ROOMS_PER_FLOOR`; use `None` for void cells
3. Cell spec formats:
   - `{"state": ROOM_STATE_BUILT, "room_type": "...", "revealed": bool}`
   - `{"state": ROOM_STATE_EMPTY, "revealed": bool}`
   - `{"state": ROOM_STATE_RUIN, "ruin_type": "...", "revealed": bool}`
4. Vision is auto-propagated at init and after any construction/clearing/demolish

### A new command
- Player (`/`): add to PLAYER_COMMANDS dict in `ui/console.py`
- Admin (`//`): add to ADMIN_COMMANDS dict in `ui/console.py`
- Multi-word admin commands (e.g. `//i am infinite`): add to the multi-word check block
  at the top of `_execute()` before the single-word parsing

### A new admin mode
1. `game_state.py`: add a bool flag field to GameState dataclass
2. `ui/console.py`: add command handler + register in `_execute()`
3. Wire the flag into the relevant system (resource checks, construction timers, etc.)

### A new resource
1. `config.py`: add INITIAL_X and INITIAL_MAX_X
2. `game_state.py`: add field to dataclass
3. `data/job_types.py`: reference in production/consumption
4. `systems/resource_system.py`: add to `_add_resource()` mapping + `_clamp_resources()`
5. `ui/resource_bar.py`: add display
6. `ui/popup.py`: add to `_res_cn()` mapping

### A new item
1. `data/items.py`: add entry to ITEM_DEFINITIONS with: key, name, description
2. `data/ruins.py`: add `rewards` to a ruin type to make it obtainable, or add a
   console/admin command to grant it
3. `ui/materials_tab.py`: it will appear automatically in the item list

### A new popup type
1. `ui/popup.py`: add `draw_xxx()` + `handle_xxx_click()`
2. `ui/renderer.py`: add to `_draw_popup_overlay()`
3. `main.py`: add to `_POPUP_HANDLERS` dict
