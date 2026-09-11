from models.event import Event
from models.location import TargetLocation

from services.event_categories import (
    search_category,
)


def search_concerts(
    location: TargetLocation | None = None,
) -> list[Event]:
    if location is None:
        events, _ = search_category(
            "conciertos"
        )

        return events

    events, _ = search_category(
        "conciertos",
        location,
    )

    return events
