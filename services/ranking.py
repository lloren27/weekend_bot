from models.event import Event


def calculate_event_score(
    event: Event
) -> int:
    score = event.source_priority

    # Datos completos
    if event.artist:
        score += 15

    if event.venue:
        score += 10

    if event.time:
        score += 5

    if event.price:
        score += 3

    if event.url:
        score += 2

    # Fuente que confirma disponibilidad
    if event.sold_out:
        score += 3

    return score


def rank_events(
    events: list[Event]
) -> list[Event]:

    for event in events:
        event.score = calculate_event_score(
            event
        )

    return sorted(
        events,
        key=lambda event: (
            -event.score,
            event.time or "99:99",
        )
    )