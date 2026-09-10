from models.event import Event

from services.event_categories import (
    limit_events_per_day,
    search_category,
)


def search_concerts() -> list[Event]:
    events, _ = search_category(
        "conciertos"
    )

    return events
