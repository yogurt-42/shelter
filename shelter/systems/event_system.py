"""Shelter — event system: periodically injects random ambient log entries."""

import time
import random
from shelter.config import EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX


def tick(state) -> list[str]:
    """Check if an event should fire. Returns log messages (if any)."""
    now = time.time()
    if now < state.last_event_time:
        return []

    # schedule next event
    state.last_event_time = now + random.uniform(EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX)

    from shelter.data.events import AMBIENT_EVENTS
    if not AMBIENT_EVENTS:
        return []

    event_text = random.choice(AMBIENT_EVENTS)
    return [event_text]
