"""Shelter — resource system: per-second tick with job-based production and passive room effects."""

import time
from shelter.config import BASE_SCRAP_PER_SEC, ROOM_STATE_BUILT


def tick(state) -> list[str]:
    """Execute one resource tick. Returns log messages (if any)."""
    now = time.time()
    dt = now - state.last_resource_tick
    state.last_resource_tick = now

    if dt <= 0:
        return []

    # --- A. baseline scrap ----
    state.scrap += BASE_SCRAP_PER_SEC * dt

    # --- B. job-based production (per assigned worker) ----
    from shelter.data.job_types import JOB_DEFINITIONS

    for job_type, workers in state.job_assignment.items():
        if workers <= 0:
            continue
        job = JOB_DEFINITIONS.get(job_type)
        if not job:
            continue
        for res_key, rate in job.get("production", {}).items():
            _add_resource(state, res_key, rate * workers * dt)
        for res_key, rate in job.get("consumption", {}).items():
            _add_resource(state, res_key, -rate * workers * dt)

    # --- C. passive room effects (per-room, worker-independent) ----
    from shelter.data.rooms import get_room

    for floor in state.floors:
        for slot in floor:
            if slot["state"] != ROOM_STATE_BUILT:
                continue
            tmpl = get_room(slot.get("room_type", ""))
            if not tmpl:
                continue

            # passive consumption (e.g. warehouse power drain)
            for res_key, rate in tmpl.get("passive_consumption", {}).items():
                _add_resource(state, res_key, -rate * dt)

            # passive production (future use)
            for res_key, rate in tmpl.get("passive_production", {}).items():
                _add_resource(state, res_key, rate * dt)

    _clamp_resources(state)
    return []


def _add_resource(state, key: str, amount: float):
    """Add/subtract a resource amount, clamped to [0, max]."""
    mapping = {
        "power": ("power", "max_power"),
        "water": ("water", "max_water"),
        "food": ("food", "max_food"),
        "scrap": ("scrap", None),
    }
    entry = mapping.get(key)
    if not entry:
        return
    attr, max_attr = entry
    val = getattr(state, attr)
    setattr(state, attr, max(0, val + amount))


def _clamp_resources(state):
    """Ensure no resource exceeds its max."""
    for attr, max_attr in [
        ("power", "max_power"),
        ("water", "max_water"),
        ("food", "max_food"),
    ]:
        cap = getattr(state, max_attr)
        current = getattr(state, attr)
        if current > cap:
            setattr(state, attr, cap)
