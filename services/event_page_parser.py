import json

from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

from models.event import Event
from services.normalizer import (
    get_source,
    calculate_score,
    get_domain,
)


GENERIC_NAMES = [
    "actividades y eventos",
    "agenda",
    "conciertos en madrid",
    "eventos en madrid",
    "espectáculos, conciertos, deportes",
    "eventos pasados",
    "la sala - del movistar arena",
    "conciertos - sala la riviera",
]


def is_generic_event_name(name: str) -> bool:
    name_lower = name.lower().strip()

    return any(
        generic in name_lower
        for generic in GENERIC_NAMES
    )


def parse_start_date(
    value: str | None
) -> tuple[date | None, str | None]:

    if not value:
        return None, None

    try:
        value = value.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            value
        )

        event_date = dt.date()

        event_time = (
            dt.strftime("%H:%M")
            if "T" in value
            else None
        )

        return event_date, event_time

    except ValueError:
        return None, None


def get_location(
    data: dict
) -> tuple[str | None, str]:

    location = data.get(
        "location"
    )

    if not isinstance(location, dict):
        return None, "Madrid"

    venue = location.get(
        "name"
    )

    address = location.get(
        "address"
    )

    municipality = "Madrid"

    if isinstance(address, dict):
        municipality = (
            address.get(
                "addressLocality"
            )
            or municipality
        )

    return venue, municipality


def get_offer_data(
    data: dict
) -> tuple[str | None, bool]:

    offers = data.get(
        "offers"
    )

    if not offers:
        return None, False

    if isinstance(offers, list):
        if not offers:
            return None, False

        offer = offers[0]

    elif isinstance(offers, dict):
        offer = offers

    else:
        return None, False

    price = offer.get(
        "price"
    )

    currency = offer.get(
        "priceCurrency",
        "EUR"
    )

    formatted_price = None

    if price is not None:
        if currency == "EUR":
            formatted_price = (
                f"{price} €"
            )
        else:
            formatted_price = (
                f"{price} {currency}"
            )

    availability = str(
        offer.get(
            "availability",
            ""
        )
    ).lower()

    sold_out = (
        "soldout" in availability
        or
        "sold_out" in availability
    )

    return (
        formatted_price,
        sold_out,
    )


def walk_json(
    node
):
    """
    Recorre recursivamente JSON-LD.

    Algunas páginas tienen:
    {
        "@graph": [...]
    }

    otras directamente una lista.
    """

    if isinstance(node, dict):

        yield node

        for value in node.values():
            yield from walk_json(
                value
            )

    elif isinstance(node, list):

        for item in node:
            yield from walk_json(
                item
            )


def is_event_node(
    node: dict
) -> bool:

    event_type = node.get(
        "@type"
    )

    if isinstance(event_type, list):
        types = event_type
    else:
        types = [event_type]

    return any(
        item in (
            "Event",
            "MusicEvent",
            "Festival",
        )
        for item in types
    )

def get_performer(
    data: dict
) -> str | None:

    performer = data.get("performer")

    if not performer:
        return None

    if isinstance(performer, dict):
        return performer.get("name")

    if isinstance(performer, list):
        names = []

        for item in performer:
            if isinstance(item, dict):
                name = item.get("name")

                if name:
                    names.append(name)

        if names:
            return ", ".join(names)

    return None

def fetch_page_events(
    url: str,
    valid_dates: set[date]
) -> list[Event]:

    try:
        response = httpx.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "WeekendBot/1.0"
                )
            },
        )

        response.raise_for_status()

    except Exception as error:
        print(
            f"⚠️ No se pudo abrir "
            f"{url}: {error}"
        )

        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    scripts = soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        }
    )

    events = []

    for script in scripts:

        if not script.string:
            continue

        try:
            data = json.loads(
                script.string
            )

        except json.JSONDecodeError:
            continue

        for node in walk_json(
            data
        ):

            if not is_event_node(
                node
            ):
                continue

            name = node.get(
                "name"
            )

            if not name:
                continue

            if is_generic_event_name(
                name
            ):
                continue

            event_date, event_time = (
                parse_start_date(
                    node.get(
                        "startDate"
                    )
                )
            )

            # Esta es nuestra validación importante.
            if event_date not in valid_dates:
                continue

            venue, municipality = (
                get_location(
                    node
                )
            )

            price, sold_out = (
                get_offer_data(
                    node
                )
            )

            event_url = (
                node.get("url")
                or url
            )

            domain = get_domain(
                event_url
            )

            event = Event(
                title=name.strip(),
                artist=get_performer(node),
                category="concert",
                date=event_date,
                time=event_time,
                venue=venue,
                municipality=municipality,
                price=price,
                sold_out=sold_out,
                source=get_source(event_url),
                url=event_url,
                description=node.get("description"),
            )

            event.score = (
                calculate_score(
                    event,
                    domain
                )
                + 40
            )

            events.append(
                event
            )

    return events
