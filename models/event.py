from dataclasses import dataclass, field
from datetime import date as Date


@dataclass
class Event:
    title: str
    category: str

    artist: str | None = None

    date: Date | None = None
    time: str | None = None

    venue: str | None = None

    municipality: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None

    price: str | None = None
    free: bool = False
    sold_out: bool = False

    source: str | None = None
    source_priority: int = 0

    url: str | None = None
    description: str | None = None

    score: int = 0

    end_date: Date | None = None
    event_type: str | None = None
    participants: list[str] = field(default_factory=list)
    address: str | None = None
    organizer: str | None = None
    external_ids: dict[str, str] = field(default_factory=dict)
    parent_event_name: str | None = None
    parent_event_url: str | None = None
    source_url: str | None = None
    original_data: dict = field(default_factory=dict)

    canonical_id: str | None = None
    sources: list[dict] = field(default_factory=list)
    match_level: str | None = None
    match_confidence: int | None = None
    field_sources: dict[str, list[str]] = field(default_factory=dict)
    conflicts: list[dict] = field(default_factory=list)
    possible_matches: list[dict] = field(default_factory=list)
    related_events: list["Event"] = field(default_factory=list)
