from copy import deepcopy
from dataclasses import fields

from services.event_identity import (
    compare_events, canonical_event_id, festival_contains,
)
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

    return compare_events(first, second).level == "MATCH"


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


METADATA_FIELDS = {
    "canonical_id", "sources", "match_level", "match_confidence", "field_sources",
    "conflicts", "possible_matches", "related_events",
}
SOURCE_FIELDS = [item.name for item in fields(Event) if item.name not in METADATA_FIELDS]


def source_snapshot(event: Event) -> dict:
    return {name: deepcopy(getattr(event, name)) for name in SOURCE_FIELDS}


def event_order(event: Event) -> tuple:
    # URLs arrive as a set from search; canonical selection must not depend on it.
    completeness = sum(bool(getattr(event, name)) for name in SOURCE_FIELDS)
    return (-event.source_priority, -completeness, event.url or "", event.title,
            repr(source_snapshot(event)))


def consolidate(group: list[Event]) -> Event:
    ordered = sorted(group, key=event_order)
    best = deepcopy(ordered[0])
    best.sources = []
    best.field_sources = {}
    best.conflicts = []
    best.possible_matches = []
    best.related_events = []
    for event in ordered:
        for act in event.related_events:
            if act not in best.related_events:
                best.related_events.append(deepcopy(act))
        for record in event.sources or [source_snapshot(event)]:
            if record not in best.sources:
                best.sources.append(deepcopy(record))
    for name in SOURCE_FIELDS:
        if name in {"original_data", "external_ids", "participants"}:
            continue
        if getattr(best, name) is None or getattr(best, name) == "":
            supplied = next((getattr(e, name) for e in ordered
                             if getattr(e, name) is not None and getattr(e, name) != ""), None)
            setattr(best, name, supplied)
        chosen = getattr(best, name)
        if name in {"sold_out", "free"}:
            chosen = any(getattr(event, name) for event in ordered)
            setattr(best, name, chosen)
        best.field_sources[name] = sorted({record.get("source_url") or record.get("url") or record.get("source") or "unknown"
                                          for record in best.sources if record.get(name) == chosen})
        values = []
        for record in best.sources:
            value = record.get(name)
            if value is not None and value != "" and value not in values:
                values.append(value)
        if len(values) > 1 and name in {"time", "end_date", "price", "free", "sold_out", "organizer", "address"}:
            best.conflicts.append({"field": name, "values": values})
    best.participants = sorted({p for e in ordered for p in e.participants})
    best.external_ids = {}
    for event in reversed(ordered):
        best.external_ids.update(event.external_ids)
    for name in ("participants", "external_ids"):
        best.field_sources[name] = sorted({r.get("source_url") or r.get("url") or r.get("source") or "unknown"
                                          for r in best.sources if r.get(name)})
    results = [compare_events(a, b) for i, a in enumerate(group) for b in group[i + 1:]]
    best.match_level = "MATCH" if len(best.sources) > 1 else None
    best.match_confidence = min((r.confidence for r in results), default=best.match_confidence)
    normalize_professional_sport_display(best)
    best.canonical_id = canonical_event_id(best)
    return best


def merge_events(first: Event, second: Event) -> Event:
    return consolidate([first, second])


def deduplicate_events(events: list[Event]) -> list[Event]:
    groups: list[list[Event]] = []
    for event in sorted(events, key=event_order):
        # Compare every source: a missing-time record must not bridge two sessions.
        candidates = [group for group in groups
                      if all(events_match(existing, event) for existing in group)]
        if len(candidates) == 1:
            candidates[0].append(event)
        else:
            groups.append([event])
    unique = [consolidate(group) for group in groups]
    # Incomplete identities can remain separate even with identical normalized
    # fields. Give each retained record a distinct reference for review.
    seen_ids = {}
    for event in unique:
        base_id = event.canonical_id
        seen_ids[base_id] = seen_ids.get(base_id, 0) + 1
        if seen_ids[base_id] > 1:
            event.canonical_id = f"{base_id}-{seen_ids[base_id]}"
    for i, first in enumerate(unique):
        for second in unique[i + 1:]:
            result = compare_events(first, second)
            if result.level == "POSSIBLE_MATCH":
                for event, other in ((first, second), (second, first)):
                    event.possible_matches.append({
                        "canonical_id": other.canonical_id, "level": result.level,
                        "confidence": result.confidence, "reasons": list(result.reasons),
                    })
    # Keep performances as separate records nested under their confirmed festival.
    # Their time, price and sources must never overwrite the festival's data.
    contained = set()
    for act in unique:
        parents = [parent for parent in unique if festival_contains(parent, act)]
        if len(parents) == 1:
            parents[0].related_events.append(deepcopy(act))
            contained.add(act.canonical_id)
    return [event for event in unique if event.canonical_id not in contained]


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
