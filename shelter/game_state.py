"""Shelter — core GameState dataclass."""

import time
import random
from dataclasses import dataclass, field
from shelter.config import (
    INITIAL_POWER,
    INITIAL_WATER,
    INITIAL_FOOD,
    INITIAL_SCRAP,
    INITIAL_MAX_POWER,
    INITIAL_MAX_WATER,
    INITIAL_MAX_FOOD,
    INITIAL_MAX_SCRAP,
    INITIAL_MAX_ITEMS,
    INITIAL_POPULATION,
    MAX_LOG_ENTRIES,
    ROOM_STATE_BUILT,
    TAB_STATUS,
    EVENT_INTERVAL_MIN,
    EVENT_INTERVAL_MAX,
)


@dataclass
class GameState:
    """Holds all runtime state for the shelter.

    This class is intentionally state-only. Room lifecycle operations
    (build, clear, upgrade, demolish, vision, capacity recalculation)
    live in `shelter.systems.room_system`.
    """

    # ---- tabs ----
    active_tab: int = TAB_STATUS
    visible_tabs: set = field(default_factory=lambda: {TAB_STATUS})

    # ---- resources ----
    power: float = INITIAL_POWER
    water: float = INITIAL_WATER
    food: float = INITIAL_FOOD
    scrap: float = INITIAL_SCRAP
    max_power: float = INITIAL_MAX_POWER
    max_water: float = INITIAL_MAX_WATER
    max_food: float = INITIAL_MAX_FOOD
    max_scrap: float = INITIAL_MAX_SCRAP

    # ---- items ----
    items: dict = field(default_factory=dict)  # item_key -> count
    max_items: int = INITIAL_MAX_ITEMS

    # ---- population ----
    population: int = INITIAL_POPULATION
    # job_type -> assigned worker count
    job_assignment: dict = field(default_factory=dict)

    # ---- admin flags ----
    infinite_resources: bool = False  # //i am infinite — no resource cost / cap
    full_speed: bool = False          # //full speed — instant build & clear

    # ---- time ----
    start_time: float = field(default_factory=time.time)
    elapsed_seconds: float = 0.0
    last_resource_tick: float = field(default_factory=time.time)
    last_event_time: float = field(
        default_factory=lambda: time.time() + random.uniform(EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX)
    )

    # ---- story system ----
    story_active: bool = True
    story_current_key: str | None = "intro"
    story_event_index: int = 0
    story_events: list = field(default_factory=list)
    story_paused: bool = False
    story_pause_tab: int | None = None
    story_last_event_time: float = 0.0
    story_popup_title: str = ""
    story_popup_text: str = ""
    story_popup_mode: str = "info"   # "info" | "choice"
    story_choices: list | None = None
    story_queue: list = field(default_factory=list)
    story_flags: dict = field(default_factory=dict)
    story_resume_tab: int | None = None  # after unlocking a tab, player must return here to resume

    # ---- log ----
    logs: list[str] = field(default_factory=list)
    log_scroll_offset: int = 0

    # ---- floors & rooms ----
    floors: list = field(default_factory=list)

    # ---- console ----
    console_input: str = ""
    console_history: list[str] = field(default_factory=list)

    # ---- build view pan offsets ----
    build_view_offset_y: float = 0.0
    build_view_offset_x: float = 0.0
    build_view_zoom: float = 1.0

    # ---- popup state ----
    popup_type: str | None = None
    popup_floor: int = 0
    popup_room: int = 0

    # ---- blueprints ----
    unlocked_blueprints: set = field(default_factory=set)

    def __post_init__(self):
        from shelter.systems import room_system
        if not self.floors:
            room_system.init_floors(self)
        room_system.recalc_caps(self)
        if not self.unlocked_blueprints:
            self.unlocked_blueprints = set()
        # Start the intro story if it hasn't been loaded from a save.
        if getattr(self, "story_active", True) and not self.story_events:
            self.story_active = False  # ensure play_story starts it immediately
            from shelter.systems import story_system
            story_system.play_intro(self)

    # ============================================================
    # Tab / blueprint helpers
    # ============================================================

    def unlock_tab(self, tab: int):
        """Make a tab visible (player must click it themselves)."""
        self.visible_tabs.add(tab)

    def unlock_blueprint(self, *keys: str):
        """Unlock one or more room blueprints."""
        for k in keys:
            self.unlocked_blueprints.add(k)

    # ============================================================
    # Popup helpers
    # ============================================================

    def open_popup(self, ptype: str, floor: int, room: int):
        self.popup_type = ptype
        self.popup_floor = floor
        self.popup_room = room

    def close_popup(self):
        self.popup_type = None

    # ============================================================
    # Room helpers (thin getters only)
    # ============================================================

    def get_room_slot(self, floor: int, room: int) -> dict:
        return self.floors[floor][room]

    # ============================================================
    # Population helpers
    # ============================================================

    @property
    def free_workers(self) -> int:
        """Workers not yet assigned to any job."""
        return self.population - sum(self.job_assignment.values())

    @property
    def assigned_workers_total(self) -> int:
        return sum(self.job_assignment.values())

    def total_job_slots(self, job_type: str) -> int:
        """Sum job_slots across all BUILT rooms providing this job_type."""
        from shelter.data.rooms import get_room

        total = 0
        for floor in self.floors:
            for slot in floor:
                if slot["state"] != ROOM_STATE_BUILT:
                    continue
                tmpl = get_room(slot.get("room_type", ""))
                if tmpl and tmpl.get("job_type") == job_type:
                    total += tmpl.get("job_slots", 0)
        return total

    def assign_worker(self, job_type: str) -> bool:
        """Try to assign one worker to a job type. Returns True on success."""
        slots = self.total_job_slots(job_type)
        current = self.job_assignment.get(job_type, 0)
        if current >= slots:
            return False
        if self.free_workers <= 0:
            return False
        self.job_assignment[job_type] = current + 1
        return True

    def unassign_worker(self, job_type: str) -> bool:
        """Remove one worker from a job type. Returns True on success."""
        current = self.job_assignment.get(job_type, 0)
        if current <= 0:
            return False
        self.job_assignment[job_type] = current - 1
        if self.job_assignment[job_type] == 0:
            del self.job_assignment[job_type]
        return True

    # ============================================================
    # Items
    # ============================================================

    def total_item_slots(self) -> int:
        """Total item slots currently occupied (each unit counts as one slot)."""
        return sum(self.items.values())

    def can_add_item(self, item_key: str, count: int = 1) -> bool:
        """Check whether adding `count` units of item_key would exceed the shared cap."""
        if count <= 0:
            return True
        return self.total_item_slots() + count <= self.max_items

    def add_item(self, item_key: str, count: int = 1) -> int:
        """Add items up to the shared cap. Returns the number actually added."""
        from shelter.data.items import get_item

        if count <= 0 or get_item(item_key) is None:
            return 0
        free = self.max_items - self.total_item_slots()
        added = min(count, free)
        if added > 0:
            self.items[item_key] = self.items.get(item_key, 0) + added
        return added

    def remove_item(self, item_key: str, count: int = 1) -> int:
        """Remove items, down to zero. Returns the number actually removed."""
        if count <= 0:
            return 0
        current = self.items.get(item_key, 0)
        removed = min(count, current)
        if removed > 0:
            self.items[item_key] = current - removed
            if self.items[item_key] == 0:
                del self.items[item_key]
        return removed

    # ============================================================
    # Log
    # ============================================================

    def add_log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > MAX_LOG_ENTRIES:
            self.logs = self.logs[-MAX_LOG_ENTRIES:]

    def add_log_and_track(self, text: str):
        self.add_log(text)
        self.log_scroll_offset = 0

    def update_time(self):
        self.elapsed_seconds = time.time() - self.start_time
        from shelter.systems import story_system
        story_system.tick(self)

    @property
    def elapsed_days(self) -> int:
        return int(self.elapsed_seconds // 86400)

    @property
    def elapsed_hours(self) -> int:
        return int((self.elapsed_seconds % 86400) // 3600)

    @property
    def elapsed_minutes(self) -> int:
        return int((self.elapsed_seconds % 3600) // 60)
