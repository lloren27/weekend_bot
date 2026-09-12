"""Conservative identity comparison; source values are never normalized in place."""
from dataclasses import dataclass
import hashlib
import json
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from models.event import Event
from services.normalizer import normalize_text, normalize_time, normalize_venue_name


@dataclass(frozen=True)
class MatchResult:
    level: str
    confidence: int
    reasons: tuple[str, ...]


def canonical_url(value: str | None) -> str:
    if not value:
        return ""
    parts = urlsplit(value)
    # Keep event/session query IDs; only discard known tracking parameters.
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                   if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid'})
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'),
                       urlencode(query), parts.fragment))


def is_festival(event: Event) -> bool:
    return (normalize_text(event.event_type) == 'festival'
            or bool(re.search(r'\b(festival|fest)\b', normalize_text(event.title))))


def title_identity(value: str | None, event: Event) -> str:
    text = normalize_text(value)
    # Remove only supplied contextual information and conventional title wrappers.
    for context in (event.venue, event.municipality):
        context = normalize_text(context)
        if context:
            text = re.sub(r'\b' + re.escape(context) + r'\b', ' ', text)
    if event.date:
        text = re.sub(r'\b' + str(event.date.year) + r'\b', ' ', text)
    text = re.sub(r'\b(festival|fest)\b', 'festival', text)
    text = re.sub(r'^(entradas?\s+(para\s+)?|concierto\s+(de\s+)?)+', '', text.strip())
    text = re.sub(r'\s+gira\s*$', '', text.strip())
    text = re.sub(r'\s+(en|at|de)\s*$', '', text.strip())
    return ' '.join(text.split())


def participant_identity(event: Event) -> str:
    if is_festival(event):
        return title_identity(event.title, event)
    return title_identity(event.artist, event)


def country_identity(value: str | None) -> str:
    text = normalize_text(value)
    return 'es' if text in {'es', 'esp', 'espana', 'spain'} else text


def event_identity(event: Event) -> dict:
    schema_type = normalize_text(event.event_type)
    kind = event.category if schema_type in {'', 'event', 'musicevent', 'sportsevent'} else schema_type
    return {
        'title': title_identity(event.title, event),
        'participant': participant_identity(event),
        'event_type': 'festival' if is_festival(event) else kind,
        'date': event.date.isoformat() if event.date else None,
        'end_date': event.end_date.isoformat() if event.end_date else None,
        'time': normalize_time(event.time),
        'venue': normalize_venue_name(event.venue),
        'city': normalize_text(event.municipality),
        'country': country_identity(event.country),
        'address': normalize_text(event.address),
        'organizer': normalize_text(event.organizer),
    }


def compare_events(first: Event, second: Event) -> MatchResult:
    a, b = event_identity(first), event_identity(second)
    equal = lambda key: bool(a[key] and a[key] == b[key])
    score = sum(weight for key, weight in (
        ('date', 30), ('venue', 25), ('city', 15), ('participant', 15),
        ('time', 10), ('title', 5)) if equal(key))
    conflicts = [key for key in ('date', 'venue', 'city', 'country', 'event_type')
                 if a[key] and b[key] and a[key] != b[key]]
    if conflicts:
        return MatchResult('DIFFERENT', score, tuple(conflicts))
    if not equal('date'):
        return MatchResult('POSSIBLE_MATCH', score, ('missing_date',))
    # An explicit range cannot be treated as a single day or an unknown range.
    if (first.end_date or first.date) != (second.end_date or second.date):
        return MatchResult('POSSIBLE_MATCH', score, ('date_range',))
    if first.category != second.category:
        return MatchResult('DIFFERENT', score, ('category',))
    if first.category == 'professional_sport':
        # Preserve the existing sports timezone-offset handling, after location guards.
        from services.deduplicator import sports_events_match
        if sports_events_match(first, second):
            return MatchResult('MATCH', max(score, 85), ('teams', 'date', 'compatible_time'))
    if first.time and second.time and (not a['time'] or not b['time'] or a['time'] != b['time']):
        return MatchResult('POSSIBLE_MATCH', score, ('time',))
    shared_id = any(value and second.external_ids.get(key) == value
                    for key, value in first.external_ids.items())
    same_title = equal('title')
    same_artist = equal('participant')
    if a['participant'] and b['participant'] and not same_artist and not is_festival(first):
        return MatchResult('DIFFERENT', score, ('participant',))
    # Same performers can offer different shows/tributes; an unqualified artist
    # title can complement a richer title, but two named shows must agree.
    named_shows = (a['title'] != a['participant'] and b['title'] != b['participant'])
    identity_agrees = same_title or (same_artist and not named_shows)
    if shared_id:
        identity_agrees = True
    if identity_agrees and (equal('venue') or shared_id):
        return MatchResult('MATCH', max(score, 80), ('identity', 'date', 'venue_or_id'))
    if identity_agrees or (equal('venue') and equal('city')):
        return MatchResult('POSSIBLE_MATCH', score, ('insufficient_identity_or_location',))
    return MatchResult('DIFFERENT', score, ('identity',))


def canonical_event_id(event: Event) -> str:
    identity = event_identity(event)
    key = {k: identity[k] for k in ('participant', 'date', 'end_date', 'time', 'venue', 'city', 'country', 'event_type')}
    key['end_date'] = key['end_date'] or key['date']
    # Title disambiguates productions by the same performer; festival title has
    # already become its participant identity. Unknowns remain explicitly empty.
    key['title'] = identity['title']
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:20]
    return f'event-{digest}'


def explicit_event_urls(event: Event) -> set[str]:
    records = event.sources or [{'url': event.url, 'original_data': event.original_data}]
    return {
        canonical_url(record['url']) for record in records
        if record.get('url') and (
            not record.get('original_data') or record['original_data'].get('url')
        )
    }


def festival_contains(festival: Event, act: Event) -> bool:
    """Presentation relationship, not equality. Never absorb multi-day sessions."""
    if not is_festival(festival) or is_festival(act) or festival.category != act.category:
        return False
    if not festival.date or festival.date != act.date:
        return False
    if (festival.end_date or festival.date) != festival.date or (act.end_date or act.date) != act.date:
        return False
    a, b = event_identity(festival), event_identity(act)
    if not a['venue'] or a['venue'] != b['venue']:
        return False
    for key in ('city', 'country'):
        if a[key] and b[key] and a[key] != b[key]:
            return False
    parent = title_identity(act.parent_event_name, festival)
    named_parent = bool(parent and parent == a['title'])
    festival_urls = explicit_event_urls(festival)
    linked_parent = bool(act.parent_event_url and canonical_url(act.parent_event_url) in {
        *festival_urls, *festival.external_ids.values()})
    shared_festival_page = bool(festival_urls & explicit_event_urls(act))
    lineup = {normalize_text(name) for name in festival.participants}
    participant = normalize_text(act.artist)
    in_lineup = bool(participant and participant in lineup)
    # A named but different parent is contradictory, even if the artist is in a lineup.
    if (parent and not named_parent) or (act.parent_event_url and not linked_parent):
        return False
    return named_parent or linked_parent or shared_festival_page or in_lineup
