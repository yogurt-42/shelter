"""Shelter — resource system: per-tick production, consumption, and caps."""

import time
from shelter.config import ROOM_STATE_BUILT, DAY_LENGTH_SECONDS


def tick(state) -> list[str]:
    """Execute one resource tick. Returns log messages (if any)."""
    now = time.time()
    dt = now - state.last_resource_tick
    state.last_resource_tick = now

    if dt <= 0:
        return []

    # Convert real seconds to in-game days.
    dt_days = dt / DAY_LENGTH_SECONDS

    # --- admin: infinite resources = skip all deductions ----
    if getattr(state, "infinite_resources", False):
        _clamp_resources(state)
        return []

    msgs = []

    # --- A. population consumption ----
    pop = state.population
    if pop > 0:
        _add_resource(state, "water", -pop * dt_days)
        _add_resource(state, "food", -pop * dt_days)

    # --- B. room-based production & consumption ----
    from shelter.data.rooms import get_room

    # Copy assigned workers so we can decrement as we allocate them to rooms.
    remaining_workers = dict(state.job_assignment)

    # Sort rooms so higher-level rooms get workers first (more efficient).
    # Simple heuristic: descending by production_per_day total value.
    def _room_priority(slot):
        tmpl = get_room(slot.get("room_type", ""))
        if not tmpl:
            return 0
        return sum(tmpl.get("production_per_day", {}).values())

    all_built = []
    for floor in state.floors:
        for slot in floor:
            if slot["state"] == ROOM_STATE_BUILT and slot.get("room_type"):
                all_built.append(slot)
    all_built.sort(key=_room_priority, reverse=True)

    for slot in all_built:
        tmpl = get_room(slot.get("room_type", ""))
        if not tmpl:
            continue

        job_type = tmpl.get("job_type")
        if job_type is None:
            continue  # passive rooms handled below

        slots = tmpl.get("job_slots", 0)
        available = remaining_workers.get(job_type, 0)
        workers_here = min(slots, available)
        if workers_here > 0:
            remaining_workers[job_type] = available - workers_here

            for res_key, rate in tmpl.get("production_per_day", {}).items():
                _add_resource(state, res_key, rate * workers_here * dt_days)
            for res_key, rate in tmpl.get("consumption_per_day", {}).items():
                _add_resource(state, res_key, -rate * workers_here * dt_days)

    # --- C. passive room effects (per-room, worker-independent) ----
    # Count rooms by type first, then apply rates.
    room_counts = {}
    for slot in all_built:
        rt = slot.get("room_type")
        if rt:
            room_counts[rt] = room_counts.get(rt, 0) + 1

    for rt, count in room_counts.items():
        tmpl = get_room(rt)
        if not tmpl:
            continue
        for res_key, rate in tmpl.get("passive_consumption_per_day", {}).items():
            _add_resource(state, res_key, -rate * count * dt_days)
        for res_key, rate in tmpl.get("passive_production", {}).items():
            _add_resource(state, res_key, rate * count * dt_days)

    # --- D. starvation warning ----
    if state.water <= 0 or state.food <= 0:
        # Only warn once per minute at most.
        last = getattr(state, "_last_starvation_warning", 0)
        if now - last > 60:
            state._last_starvation_warning = now
            if state.water <= 0:
                msgs.append("警告：水已耗尽，人口健康状态恶化。")
            if state.food <= 0:
                msgs.append("警告：食物已耗尽，人口健康状态恶化。")

    _clamp_resources(state)
    return msgs


def _add_resource(state, key: str, amount: float):
    """Add/subtract a resource amount, clamped to [0, max]."""
    mapping = {
        "power": ("power", "max_power"),
        "water": ("water", "max_water"),
        "food": ("food", "max_food"),
        "scrap": ("scrap", "max_scrap"),
    }
    entry = mapping.get(key)
    if not entry:
        return
    attr, max_attr = entry
    val = getattr(state, attr)
    new_val = val + amount
    if max_attr is not None:
        new_val = min(new_val, getattr(state, max_attr))
    setattr(state, attr, max(0, new_val))


def _clamp_resources(state):
    """Ensure no resource exceeds its max."""
    for attr, max_attr in [
        ("power", "max_power"),
        ("water", "max_water"),
        ("food", "max_food"),
        ("scrap", "max_scrap"),
    ]:
        cap = getattr(state, max_attr)
        current = getattr(state, attr)
        if current > cap:
            setattr(state, attr, cap)
