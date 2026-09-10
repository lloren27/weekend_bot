from models.event import Event
from services.normalizer import (
    normalize_text,
    normalize_venue_name,
    to_text,
)


TEAM_ALIASES = {
    "deportivo": "rc deportivo",
    "deportivo la coruna": "rc deportivo",
    "deportivo de a coruna": "rc deportivo",
    "rc deportivo": "rc deportivo",
    "r c deportivo": "rc deportivo",
    "real madrid cf": "real madrid",
    "real madrid": "real madrid",
    "rayo": "rayo vallecano",
    "rayo vallecano": "rayo vallecano",
    "getafe": "getafe cf",
    "getafe cf": "getafe cf",
    "club atletico de madrid": "atletico madrid",
    "atletico de madrid": "atletico madrid",
    "atletico madrid": "atletico madrid",
    "cd leganes": "cd leganes",
    "leganes": "cd leganes",
    "madrid cf": "madrid cff",
    "madrid cff": "madrid cff",
    "sevilla fc": "sevilla fc",
    "sevilla": "sevilla fc",
}


TEAM_DISPLAY_NAMES = {
    "atletico madrid": "Atlético de Madrid",
    "cd leganes": "CD Leganés",
    "getafe cf": "Getafe CF",
    "madrid cff": "Madrid CFF",
    "rayo vallecano": "Rayo Vallecano",
    "rc deportivo": "RC Deportivo",
    "real madrid": "Real Madrid",
    "sevilla fc": "Sevilla FC",
}


HOME_TEAM_BY_VENUE = {
    "santiago bernabeu": "real madrid",
    "riyadh air metropolitano": "atletico madrid",
    "estadio de vallecas": "rayo vallecano",
    "coliseum": "getafe cf",
    "estadio municipal de butarque": "cd leganes",
    "estadio fernando torres": "madrid cff",
}


NON_TEAM_TERMS = {
    "la liga",
    "laliga",
    "liga",
    "liga f",
    "liga endesa",
    "acb",
    "euroliga",
    "euroleague",
    "champions league",
    "uefa",
    "copa del rey",
    "primera division",
    "segunda division",
    "partido",
    "match",
    "entradas",
    "tickets",
}


def events_match(
    first: Event,
    second: Event
) -> bool:

    if first.date != second.date:
        return False

    if sports_events_match(
        first,
        second,
    ):
        return True

    first_artist = normalize_text(
        first.artist
    )

    second_artist = normalize_text(
        second.artist
    )

    # Si ambas fuentes conocen artista,
    # artista + fecha es una señal muy fuerte.
    if first_artist and second_artist:
        if first_artist != second_artist:
            return False

        first_venue = normalize_venue_name(
            first.venue
        )

        second_venue = normalize_venue_name(
            second.venue
        )

        # Si ambos conocen recinto y es diferente,
        # asumimos que podrían ser eventos distintos.
        if (
            first_venue
            and second_venue
            and first_venue != second_venue
        ):
            return False

        return True

    # Si no tenemos artista,
    # intentamos título exacto normalizado.
    return (
        normalize_text(first.title)
        ==
        normalize_text(second.title)
    )


def sports_events_match(
    first: Event,
    second: Event,
) -> bool:
    if (
        first.category != "professional_sport"
        or second.category != "professional_sport"
    ):
        return False

    first_venue = normalize_venue_name(
        first.venue
    )

    second_venue = normalize_venue_name(
        second.venue
    )

    if (
        first_venue
        and second_venue
        and first_venue != second_venue
    ):
        return False

    first_teams = extract_team_set(
        first
    )

    second_teams = extract_team_set(
        second
    )

    if (
        len(first_teams) < 2
        or first_teams != second_teams
    ):
        return False

    return times_are_compatible(
        first.time,
        second.time,
    )


def times_are_compatible(
    first_time: str | None,
    second_time: str | None,
) -> bool:
    if (
        not first_time
        or not second_time
    ):
        return True

    if first_time == second_time:
        return True

    first_minutes = parse_minutes(
        first_time
    )

    second_minutes = parse_minutes(
        second_time
    )

    if (
        first_minutes is None
        or second_minutes is None
    ):
        return False

    return (
        abs(first_minutes - second_minutes)
        <= 120
    )


def parse_minutes(
    value: str
) -> int | None:
    try:
        hours, minutes = value.split(
            ":",
            1,
        )

        return (
            int(hours) * 60
            + int(minutes)
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def extract_team_set(
    event: Event
) -> frozenset[str]:
    for value in (
        event.artist,
        event.title,
    ):
        teams = parse_team_set(
            value
        )

        if len(teams) >= 2:
            return teams

    return frozenset()


def parse_team_set(
    value: str | None
) -> frozenset[str]:
    raw_text = to_text(
        value
    )

    if not raw_text:
        return frozenset()

    raw_text = (
        raw_text
        .replace(",", " vs ")
        .replace("@", " vs ")
        .replace("-", " vs ")
        .replace("–", " vs ")
        .replace("—", " vs ")
    )

    text = normalize_text(
        raw_text
    )

    if not text:
        return frozenset()

    parts = text.split(
        " vs "
    )

    split_parts = []

    for part in parts:
        split_parts.extend(
            part.split(
                " v "
            )
        )

    teams = {
        normalize_team_name(part)
        for part in split_parts
        if normalize_team_name(part)
    }

    return frozenset(
        teams
    )


def normalize_team_name(
    value: str
) -> str:
    team = normalize_text(
        value
    )

    if not team:
        return ""

    if team in NON_TEAM_TERMS:
        return ""

    return TEAM_ALIASES.get(
        team,
        team,
    )


def merge_events(
    first: Event,
    second: Event
) -> Event:

    if (
        second.source_priority
        > first.source_priority
    ):
        best = second
        other = first

    else:
        best = first
        other = second

    if not best.artist:
        best.artist = other.artist

    if not best.time:
        best.time = other.time

    if not best.venue:
        best.venue = other.venue

    if not best.price:
        best.price = other.price

    if not best.description:
        best.description = other.description

    if not best.url:
        best.url = other.url

    # Si cualquier fuente confirma sold out,
    # conservamos la información.
    best.sold_out = (
        best.sold_out
        or other.sold_out
    )

    best.free = (
        best.free
        or other.free
    )

    normalize_professional_sport_display(
        best
    )

    return best


def deduplicate_events(
    events: list[Event]
) -> list[Event]:

    unique = []

    for event in events:

        duplicate_index = None

        for index, existing in enumerate(
            unique
        ):
            if events_match(
                existing,
                event
            ):
                duplicate_index = index
                break

        if duplicate_index is None:
            normalize_professional_sport_display(
                event
            )

            unique.append(event)

        else:
            unique[duplicate_index] = (
                merge_events(
                    unique[duplicate_index],
                    event,
                )
            )

    return unique


def normalize_professional_sport_display(
    event: Event
) -> None:
    if event.category != "professional_sport":
        return

    teams = extract_team_set(
        event
    )

    if len(teams) < 2:
        return

    venue = normalize_venue_name(
        event.venue
    )

    home_team = HOME_TEAM_BY_VENUE.get(
        venue
    )

    if (
        home_team
        and home_team in teams
    ):
        ordered_teams = [
            home_team,
            *sorted(
                team
                for team in teams
                if team != home_team
            ),
        ]

    else:
        ordered_teams = sorted(
            teams
        )

    display_name = " - ".join(
        TEAM_DISPLAY_NAMES.get(
            team,
            team.title(),
        )
        for team in ordered_teams
    )

    event.artist = display_name
    event.title = display_name
