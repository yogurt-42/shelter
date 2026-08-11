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
    FLOORS,
    ROOMS_PER_FLOOR,
    ROOM_STATE_EMPTY,
    ROOM_STATE_RUIN,
    ROOM_STATE_BUILT,
    ROOM_STATE_BUILDING,
    ROOM_STATE_CLEARING,
    TAB_STATUS,
    TAB_BUILD,
    TAB_POPULATION,
    TAB_MATERIALS,
    EVENT_INTERVAL_MIN,
    EVENT_INTERVAL_MAX,
)


def _make_room_slot(state: int, ruin_type: str | None = None) -> dict:
    return {
        "state": state,
        "room_type": None,
        "level": 1,
        "ruin_type": ruin_type,
        "assigned_workers": 0,
        "build_end_time": None,
        "action_type": None,  # "building" | "clearing" | None
    }


@dataclass
class GameState:
    """Holds all runtime state for the shelter."""

    # ---- tabs ----
    active_tab: int = TAB_STATUS
    visible_tabs: set = field(default_factory=lambda: {TAB_STATUS, TAB_BUILD, TAB_POPULATION, TAB_MATERIALS})

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

    # ---- popup state ----
    # popup_type: None | "build" | "room_info" | "ruin_info" | "room_action"
    popup_type: str | None = None
    popup_floor: int = 0
    popup_room: int = 0

    def __post_init__(self):
        if not self.logs:
            self.logs = [
                "避难所主控 AI 已重新激活。正在自检...",
                "自检完成。核心系统正常，备用电源已接入。",
                "检测到拾荒者信号。他们触发了入口机关。",
                "基础协议已加载。等待管理者指令。",
                "避难所状态：第1层部分可用，第2-5层均为废墟。需要立即修复。",
            ]
        if not self.floors:
            self._init_floors()

    def _init_floors(self):
        """Initialize floors with varied ruin types per the layout table."""
        from shelter.data.ruins import get_ruin_for_slot

        self.floors = []
        for f in range(FLOORS):
            row = []
            for r in range(ROOMS_PER_FLOOR):
                if f == 0 and r < 3:
                    slot = _make_room_slot(ROOM_STATE_EMPTY)
                else:
                    ruin_key = get_ruin_for_slot(f, r)
                    slot = _make_room_slot(ROOM_STATE_RUIN, ruin_type=ruin_key)
                row.append(slot)
            self.floors.append(row)

    # ---- popup helpers ----

    def open_popup(self, ptype: str, floor: int, room: int):
        self.popup_type = ptype
        self.popup_floor = floor
        self.popup_room = room

    def close_popup(self):
        self.popup_type = None

    # ---- room helpers ----

    def get_room_slot(self, floor: int, room: int) -> dict:
        return self.floors[floor][room]

    def start_building(self, floor: int, room: int, room_key: str, build_time: float):
        slot = self.get_room_slot(floor, room)
        slot["state"] = ROOM_STATE_BUILDING
        slot["room_type"] = room_key
        if self.full_speed:
            build_time = 0
        slot["build_end_time"] = time.time() + build_time
        slot["action_type"] = "building"

    def start_clearing(self, floor: int, room: int, clear_time: float):
        slot = self.get_room_slot(floor, room)
        slot["state"] = ROOM_STATE_CLEARING
        if self.full_speed:
            clear_time = 0
        slot["build_end_time"] = time.time() + clear_time
        slot["action_type"] = "clearing"

    def complete_construction(self, floor: int, room: int):
        """Called when a build/clear timer finishes."""
        slot = self.get_room_slot(floor, room)
        action = slot["action_type"]
        if action == "building":
            slot["state"] = ROOM_STATE_BUILT
            slot["level"] = 1
            slot["assigned_workers"] = 0
            self._apply_build_effect(slot.get("room_type"))
        elif action == "clearing":
            ruin_type = slot.get("ruin_type")
            slot["state"] = ROOM_STATE_EMPTY
            slot["ruin_type"] = None
            self._award_ruin_rewards(ruin_type)
        slot["build_end_time"] = None
        slot["action_type"] = None

    def _apply_build_effect(self, room_type: str | None):
        """Apply one-time effects when a room finishes construction."""
        if not room_type:
            return
        from shelter.data.rooms import get_room

        tmpl = get_room(room_type)
        if not tmpl:
            return
        effect = tmpl.get("on_built_effect")
        if effect == "increase_scrap_cap_50":
            self.max_scrap += 50
            self.add_log(f"仓库扩容：废料上限 +50（当前 {int(self.max_scrap)}）")
        elif effect == "increase_scrap_cap_100":
            self.max_scrap += 100
            self.add_log(f"大型仓库扩容：废料上限 +100（当前 {int(self.max_scrap)}）")

    def _award_ruin_rewards(self, ruin_type: str | None):
        """Award items when a ruin is cleared."""
        if not ruin_type:
            return
        from shelter.data.ruins import RUIN_TYPES
        from shelter.data.items import get_item

        ruin_data = RUIN_TYPES.get(ruin_type)
        if not ruin_data:
            return
        for reward in ruin_data.get("rewards", []):
            item_key = reward.get("item")
            count = reward.get("count", 1)
            if not item_key or get_item(item_key) is None:
                continue
            added = self.add_item(item_key, count)
            if added > 0:
                item_name = get_item(item_key)["name"]
                self.add_log(f"清理废墟获得：{item_name} x{added}")
            if added < count:
                self.add_log("物品栏已满，部分奖励已丢失。")

    # ---- population helpers ----

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

    # ---- items ----

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

    # ---- log ----

    def add_log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > MAX_LOG_ENTRIES:
            self.logs = self.logs[-MAX_LOG_ENTRIES:]

    def add_log_and_track(self, text: str):
        self.add_log(text)
        self.log_scroll_offset = 0

    def update_time(self):
        self.elapsed_seconds = time.time() - self.start_time

    @property
    def elapsed_days(self) -> int:
        return int(self.elapsed_seconds // 86400)

    @property
    def elapsed_hours(self) -> int:
        return int((self.elapsed_seconds % 86400) // 3600)

    @property
    def elapsed_minutes(self) -> int:
        return int((self.elapsed_seconds % 3600) // 60)
