# CLAUDE.md — AI Developer Onboarding

Project: **Shelter** — post-apocalyptic underground shelter management text game.
Single-developer Python + Pygame desktop app. Terminal aesthetic, monochrome palette,
Chinese player-facing text, English codebase.

## Quickstart

```bash
cd D:/project_s/demo && python -m shelter.main          # launch game
cd D:/project_s/demo && python -c "from shelter.game_state import GameState; ..."  # REPL testing
```

## Tech

- Python 3.12, Pygame 2.6, stdlib dataclasses
- No external deps beyond Pygame
- Font: SimHei (CJK) with Consolas fallback
- 1100×700 window, 30 FPS, single-threaded game loop

## Directory Map (~2600 LOC)

```
shelter/
├── main.py                     # entry: init pygame → event loop → tick → render
├── config.py                   # ALL constants (window, colors, fonts, layout, pacing)
├── game_state.py               # @dataclass GameState — single source of truth
├── data/                       # static definitions (read-only at runtime)
│   ├── rooms.py                # ROOM_TEMPLATES dict, get_room(), list_buildable()
│   ├── ruins.py                # RUIN_TYPES, can_clear(), evaluate_condition()
│   ├── job_types.py            # JOB_DEFINITIONS, get_job()
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
    ├── build_tab.py            # 5-floor × 6-room pannable map + drag + click routing
    ├── population_tab.py       # job-type aggregation, worker assignment
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
| Resources | `power, water, food, scrap: float` + `max_power, max_water, max_food` |
| Population | `population: int`, `job_assignment: dict[str,int]` (job_type→workers) |
| Floors | `floors: list[list[dict]]` — 5 floors × 6 rooms, each slot: `{state, room_type, level, ruin_type, build_end_time, action_type}` |
| UI state | `console_input`, `console_history`, `logs`, `log_scroll_offset`, `build_view_offset_x/y` |
| Popup | `popup_type: str\|None`, `popup_floor`, `popup_room` |
| Time | `elapsed_seconds`, `last_resource_tick`, `last_event_time` |

Key methods: `open_popup()`, `close_popup()`, `start_building()`, `start_clearing()`,
`complete_construction()`, `free_workers`, `total_job_slots(job_type)`,
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
- Console: `handle_key(event, state) -> bool`
- Popup: `draw_xxx(surface, state, fonts)` + `handle_xxx_click(pos, state) -> bool`

### Room State Machine

```
EMPTY(0) ──[build click]──► BUILDING(3) ──[timer]──► BUILT(2)
RUIN(1) ──[clear click]──► CLEARING(4) ──[timer]──► EMPTY(0)
BUILT(2) ──[right-click]──► upgrade / downgrade / demolish
```

Room slot dict: `{"state": int, "room_type": str|None, "level": int,
"ruin_type": str|None, "build_end_time": float|None, "action_type": str|None}`

### Job/Population Model

- Rooms define `job_type` (str key into JOB_DEFINITIONS) + `job_slots` (int)
- Same-type room slots aggregate: 2 generators = 4 "power_tech" slots
- `state.job_assignment: {job_type: workers}` — assigned per type, NOT per room
- `state.free_workers = population - sum(job_assignment.values())`
- Resource production: `workers × per_worker_rate × dt` (from JOB_DEFINITIONS)
- Passive rooms (warehouse): `job_slots=0`, drain resources via `passive_consumption`

### Config Constants

```
TAB_STATUS=0, TAB_BUILD=1, TAB_POPULATION=2
ROOM_STATE_EMPTY=0, RUIN=1, BUILT=2, BUILDING=3, CLEARING=4
FLOORS=5, ROOMS_PER_FLOOR=6
POPUP_WIDTH=520, POPUP_MAX_HEIGHT=560
INITIAL_POPULATION=5, INITIAL_SCRAP=200, INITIAL_POWER=100
```

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
   clear_cost, clear_time, conditions[]
2. Add conditions using types: `has_resources`, `has_room`, `stat_check`
3. Assign to slots via INITIAL_RUIN_LAYOUT dict

### A new command
- Player (`/`): add to PLAYER_COMMANDS dict in `ui/console.py`
- Admin (`//`): add to ADMIN_COMMANDS dict in `ui/console.py`

### A new resource
1. `config.py`: add INITIAL_X and INITIAL_MAX_X
2. `game_state.py`: add field to dataclass
3. `data/job_types.py`: reference in production/consumption
4. `systems/resource_system.py`: add to `_add_resource()` mapping + `_clamp_resources()`
5. `ui/resource_bar.py`: add display
6. `ui/popup.py`: add to `_res_cn()` mapping

### A new popup type
1. `ui/popup.py`: add `draw_xxx()` + `handle_xxx_click()`
2. `ui/renderer.py`: add to `_draw_popup_overlay()`
3. `main.py`: add to `_POPUP_HANDLERS` dict
