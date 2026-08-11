"""Shelter — centralized constants. Edit here to adjust game parameters."""

# ============================================================
# Window
# ============================================================
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
WINDOW_TITLE = "SHELTER — 避难所主控台"
FPS = 30

# ============================================================
# Colors (monochrome: black / gray / white only)
# ============================================================
COLOR_BG = (0, 0, 0)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_BRIGHT = (200, 200, 200)
COLOR_TEXT_DIM = (120, 120, 120)
COLOR_TEXT_MID = (160, 160, 160)
COLOR_BORDER = (60, 60, 60)
COLOR_BORDER_LIGHT = (100, 100, 100)

# Room cell colors
COLOR_CELL_EMPTY_BG = (35, 35, 35)
COLOR_CELL_RUIN_BG = (55, 55, 55)
COLOR_CELL_BUILT_BG = (75, 75, 75)
COLOR_CELL_HOVER_BORDER = (180, 180, 180)

# Tab bar
COLOR_TAB_ACTIVE_TEXT = (255, 255, 255)
COLOR_TAB_ACTIVE_UNDERLINE = (200, 200, 200)
COLOR_TAB_INACTIVE_TEXT = (100, 100, 100)

# Resource bar
COLOR_RESOURCE_BG = (18, 18, 18)
COLOR_RESOURCE_LABEL = (140, 140, 140)
COLOR_RESOURCE_VALUE = (220, 220, 220)

# Console
COLOR_CONSOLE_BG = (15, 15, 15)
COLOR_CONSOLE_PROMPT = (180, 180, 180)
COLOR_CONSOLE_TEXT = (200, 200, 200)
COLOR_CONSOLE_CURSOR = (180, 180, 180)

# ============================================================
# Fonts
# ============================================================
FONT_NAME_CJK = "SimHei"
FONT_NAME_MONO = "Consolas"
FONT_SIZE_SMALL = 14
FONT_SIZE_NORMAL = 16
FONT_SIZE_LARGE = 20
FONT_SIZE_TITLE = 24

# ============================================================
# Layout
# ============================================================
TAB_BAR_HEIGHT = 30
RESOURCE_BAR_HEIGHT = 28
CONSOLE_HEIGHT = 30
MAIN_AREA_Y = TAB_BAR_HEIGHT + RESOURCE_BAR_HEIGHT
MAIN_AREA_HEIGHT = WINDOW_HEIGHT - MAIN_AREA_Y - CONSOLE_HEIGHT

# ============================================================
# Map / build view
# ============================================================
FLOORS = 5
ROOMS_PER_FLOOR = 6
ROOM_CELL_WIDTH = 140
ROOM_CELL_HEIGHT = 58
ROOM_CELL_PADDING = 6
MAP_LEFT_MARGIN = 20
MAP_TOP_MARGIN = 10

# Room state enum
ROOM_STATE_EMPTY = 0
ROOM_STATE_RUIN = 1
ROOM_STATE_BUILT = 2
ROOM_STATE_BUILDING = 3   # construction in progress
ROOM_STATE_CLEARING = 4   # ruin clearing in progress

# Popup window
POPUP_WIDTH = 520
POPUP_MAX_HEIGHT = 560

# Tab keys
TAB_STATUS = 0
TAB_BUILD = 1
TAB_POPULATION = 2
TAB_MATERIALS = 3

# ============================================================
# Population
# ============================================================
INITIAL_POPULATION = 5

# ============================================================
# Game pacing
# ============================================================
GAME_TICK_INTERVAL = 1.0

# ============================================================
# Initial resources
# ============================================================
INITIAL_POWER = 100
INITIAL_WATER = 50
INITIAL_FOOD = 30
INITIAL_SCRAP = 200

INITIAL_MAX_POWER = 200
INITIAL_MAX_WATER = 100
INITIAL_MAX_FOOD = 100

INITIAL_MAX_SCRAP = 300
INITIAL_MAX_ITEMS = 20

MAX_LOG_ENTRIES = 200

# ============================================================
# Mini-log panel (shown at bottom of build tab)
# ============================================================
MINI_LOG_HEIGHT = 75
MINI_LOG_LINES = 3
MINI_LOG_BG = (12, 12, 12)

# ============================================================
# Build view drag limits
# ============================================================
BUILD_DRAG_LIMIT_Y = 150
BUILD_DRAG_LIMIT_X = 600

# ============================================================
# Base resource rates (per second, without rooms)
# ============================================================
BASE_SCRAP_PER_SEC = 0.1
# Power, water, food have no production without rooms

# ============================================================
# Random event intervals
# ============================================================
EVENT_INTERVAL_MIN = 5.0
EVENT_INTERVAL_MAX = 15.0
