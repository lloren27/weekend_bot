from dataclasses import dataclass
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