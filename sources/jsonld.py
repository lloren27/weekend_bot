import json
import logging
from copy import deepcopy
from urllib.parse import urljoin, urlsplit

from datetime import date, datetime

import httpx

from bs4 import BeautifulSoup

from config import CACHE_TTL_SECONDS
from models.event import Event

from services.cache import TTLCache
from services.normalizer import to_text
from services.event_identity import canonical_url

from services.source_registry import (
    get_source_info,
)


EVENT_TYPES = {
    "Event",
    "MusicEvent",
    "Festival",
}

_PAGE_CACHE = TTLCache(
    CACHE_TTL_SECONDS
)

logger = logging.getLogger(__name__)


def normalize_schema_type(
    value
) -> str:
    event_type = to_text(
        value
    )

    if not event_type:
        return ""

    if "/" in event_type:
        event_type = event_type.rstrip(
            "/"
        ).rsplit(
            "/",
            1,
        )[-1]

    if ":" in event_type:
        event_type = event_type.rsplit(
            ":",
            1,
        )[-1]

    return event_type


def walk_json(node):
    """
    Recorre recursivamente cualquier estructura JSON-LD.

    Puede recibir:
    - dict
    - list
    - @graph
    - objetos anidados
    """

    if isinstance(node, dict):
        yield node

        for value in node.values():
            yield from walk_json(value)

    elif isinstance(node, list):
        for item in node:
            yield from walk_json(item)


def walk_event_nodes(node, parent=None):
    """Retain explicit schema.org subEvent relationships while traversing."""
    if isinstance(node, dict):
        yield node, parent
        for key, value in node.items():
            yield from walk_event_nodes(value, node if key in {"subEvent", "subEvents"} else None)
    elif isinstance(node, list):
        for item in node:
            yield from walk_event_nodes(item, parent)


def identity_metadata(node: dict, source_url: str, parent=None) -> dict:
    performers = node.get("performer") or []
    if not isinstance(performers, list):
        performers = [performers]
    participants = [to_text(p) for p in performers if to_text(p)]
    types = node.get("@type", [])
    if not isinstance(types, list):
        types = [types]
    types = [normalize_schema_type(t) for t in types]
    external_ids = {}
    if to_text(node.get("@id")):
        external_ids["@id"] = canonical_url(urljoin(source_url, to_text(node["@id"])))
    identifier = to_text(node.get("identifier"))
    if identifier:
        external_ids[urlsplit(source_url).netloc.lower()] = identifier
    parent = node.get("superEvent") or parent or {}
    if isinstance(parent, dict):
        parent_name = to_text(parent.get("name")) or None
        parent_url = to_text(parent.get("url")) or to_text(parent.get("@id"))
    else:
        parent_name, parent_url = None, to_text(parent)
    location = node.get("location") or {}
    if isinstance(location, list):
        location = next((item for item in location if isinstance(item, dict)), {})
    address = location.get("address") if isinstance(location, dict) else None
    street = to_text(address.get("streetAddress")) if isinstance(address, dict) else to_text(address)
    return {
        "end_date": parse_datetime(node.get("endDate"))[0],
        "event_type": "Festival" if "Festival" in types else next(iter(types), None),
        "participants": participants,
        "address": street or None,
        "organizer": to_text(node.get("organizer")) or None,
        "external_ids": external_ids,
        "parent_event_name": parent_name,
        "parent_event_url": urljoin(source_url, parent_url) if parent_url else None,
        "source_url": source_url,
        "original_data": deepcopy(node),
    }


def is_event(
    node: dict,
    allowed_types: set[str] | None = None,
) -> bool:
    """
    Comprueba si un nodo JSON-LD representa
    un tipo de evento permitido.
    """

    event_type = node.get("@type")

    if isinstance(event_type, list):
        types = {
            normalize_schema_type(item)
            for item in event_type
            if normalize_schema_type(item)
        }

    else:
        value = normalize_schema_type(
            event_type
        )

        types = {
            value
        } if value else set()

    if allowed_types is None:
        allowed_types = EVENT_TYPES

    return bool(
        types.intersection(
            allowed_types
        )
    )


def parse_datetime(
    value
) -> tuple[date | None, str | None]:
    """
    Convierte startDate de JSON-LD a:

    (
        fecha,
        hora
    )

    Ejemplos soportados:
    2026-09-11
    2026-09-11T21:00:00
    2026-09-11T21:00:00+02:00
    2026-09-11T19:00:00Z
    """

    text = to_text(value)

    if not text:
        return None, None

    try:
        clean_value = text.replace(
            "Z",
            "+00:00"
        )

        parsed = datetime.fromisoformat(
            clean_value
        )

        event_date = parsed.date()

        event_time = None

        if "T" in text:
            event_time = parsed.strftime(
                "%H:%M"
            )

        return (
            event_date,
            event_time,
        )

    except ValueError:
        try:
            parsed_date = date.fromisoformat(
                text[:10]
            )

            return (
                parsed_date,
                None,
            )

        except ValueError:
            return (
                None,
                None,
            )


def extract_performer(
    node: dict
) -> str | None:
    """
    Extrae uno o varios artistas.

    JSON-LD puede devolver:

    performer: {
        "name": "Aitana"
    }

    o:

    performer: [
        {"name": "Artista 1"},
        {"name": "Artista 2"}
    ]
    """

    performer = node.get(
        "performer"
    )

    if not performer:
        return None

    if isinstance(
        performer,
        list
    ):
        names = []

        for item in performer:

            if isinstance(
                item,
                dict
            ):
                name = to_text(
                    item.get("name")
                )

            else:
                name = to_text(
                    item
                )

            if name:
                names.append(
                    name
                )

        if names:
            return ", ".join(
                names
            )

        return None

    if isinstance(
        performer,
        dict
    ):
        name = to_text(
            performer.get("name")
        )

        return (
            name
            or None
        )

    name = to_text(
        performer
    )

    return (
        name
        or None
    )


def extract_country(
    value
) -> str | None:
    """
    addressCountry puede aparecer como:

    "ES"

    o:

    {
        "@type": "Country",
        "name": "España"
    }
    """

    if not value:
        return None

    if isinstance(
        value,
        dict
    ):
        country = (
            to_text(
                value.get("name")
            )
            or to_text(
                value.get("@id")
            )
        )

        return (
            country
            or None
        )

    country = to_text(
        value
    )

    return (
        country
        or None
    )


def extract_location(
    node: dict
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
]:
    """
    Devuelve:

    (
        venue,
        municipality,
        region,
        postal_code,
        country
    )
    """

    location = node.get(
        "location"
    )

    # Algunas fuentes pueden devolver
    # varias localizaciones.
    # Por ahora utilizamos la primera válida.
    if isinstance(
        location,
        list
    ):
        location = next(
            (
                item
                for item in location
                if isinstance(item, dict)
            ),
            None,
        )

    if not isinstance(
        location,
        dict
    ):
        return (
            None,
            None,
            None,
            None,
            None,
        )

    venue = (
        to_text(
            location.get("name")
        )
        or None
    )

    address = location.get(
        "address"
    )

    municipality = None
    region = None
    postal_code = None
    country = None

    if isinstance(
        address,
        dict
    ):
        municipality = (
            to_text(
                address.get(
                    "addressLocality"
                )
            )
            or None
        )

        region = (
            to_text(
                address.get(
                    "addressRegion"
                )
            )
            or None
        )

        postal_code = (
            to_text(
                address.get(
                    "postalCode"
                )
            )
            or None
        )

        country = extract_country(
            address.get(
                "addressCountry"
            )
        )

    return (
        venue,
        municipality,
        region,
        postal_code,
        country,
    )


def extract_offer(
    node: dict
) -> tuple[str | None, bool]:
    """
    Extrae precio y disponibilidad.

    Devuelve:
    (
        precio,
        sold_out
    )
    """

    offers = node.get(
        "offers"
    )

    if not offers:
        return (
            None,
            False,
        )

    offer = None

    if isinstance(
        offers,
        list
    ):
        offer = next(
            (
                item
                for item in offers
                if isinstance(item, dict)
            ),
            None,
        )

    elif isinstance(
        offers,
        dict
    ):
        offer = offers

    if not offer:
        return (
            None,
            False,
        )

    price = to_text(
        offer.get(
            "price"
        )
    )

    currency = (
        to_text(
            offer.get(
                "priceCurrency"
            )
        )
        or "EUR"
    )

    price_text = None

    if price:

        if currency.upper() == "EUR":
            price_text = (
                f"{price} €"
            )

        else:
            price_text = (
                f"{price} {currency}"
            )

    availability = to_text(
        offer.get(
            "availability"
        )
    ).lower()

    sold_out = (
        "soldout" in availability
        or "sold_out" in availability
        or "sold-out" in availability
    )

    return (
        price_text,
        sold_out,
    )


def fetch_page_text(
    url: str,
) -> str | None:
    cached_text = _PAGE_CACHE.get(
        url
    )

    if cached_text is not None:
        return cached_text

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
        logger.warning(
            "No se pudo abrir %s: %s",
            url,
            error,
        )

        return None

    _PAGE_CACHE.set(
        url,
        response.text,
    )

    return response.text


def clear_page_cache() -> None:
    _PAGE_CACHE.clear()


def extract_events_from_url(
    url: str,
    valid_dates: set[date],
    category: str = "concert",
    allowed_types: set[str] | None = None,
) -> list[Event]:
    """
    Descarga una página y extrae los eventos
    definidos mediante JSON-LD/schema.org.
    """

    page_text = fetch_page_text(
        url
    )

    if page_text is None:
        return []

    soup = BeautifulSoup(
        page_text,
        "html.parser"
    )

    scripts = soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        }
    )

    events: list[Event] = []

    for script in scripts:

        raw = (
            script.string
            or script.get_text(
                strip=True
            )
        )

        if not raw:
            continue

        try:
            json_data = json.loads(
                raw
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

        for node, parent in walk_event_nodes(
            json_data
        ):

            if not isinstance(
                node,
                dict
            ):
                continue

            if not is_event(
                node,
                allowed_types=allowed_types,
            ):
                continue

            # =========================
            # TÍTULO
            # =========================

            title = to_text(
                node.get("name")
            )

            if not title:
                continue

            # =========================
            # FECHA / HORA
            # =========================

            event_date, event_time = (
                parse_datetime(
                    node.get(
                        "startDate"
                    )
                )
            )

            # Fuera del fin de semana
            # solicitado = descartado.

            if event_date not in valid_dates:
                continue

            # =========================
            # LOCALIZACIÓN
            # =========================

            (
                venue,
                municipality,
                region,
                postal_code,
                country,
            ) = extract_location(
                node
            )

            # =========================
            # PRECIO
            # =========================

            price, sold_out = (
                extract_offer(
                    node
                )
            )

            # =========================
            # URL
            # =========================

            event_url = (
                to_text(
                    node.get(
                        "url"
                    )
                )
                or url
            )

            # Calculamos la fuente utilizando
            # la URL específica del evento
            # siempre que exista.

            source_name, priority = (
                get_source_info(
                    event_url
                )
            )

            # =========================
            # DESCRIPCIÓN
            # =========================

            description = (
                to_text(
                    node.get(
                        "description"
                    )
                )
                or None
            )

            # =========================
            # EVENT
            # =========================

            events.append(
                Event(
                    title=title,

                    artist=extract_performer(
                        node
                    ),

                    category=category,

                    date=event_date,
                    time=event_time,

                    venue=venue,

                    municipality=municipality,
                    region=region,
                    postal_code=postal_code,
                    country=country,

                    price=price,
                    sold_out=sold_out,

                    source=source_name,
                    source_priority=priority,

                    url=event_url,

                    description=description,
                    **identity_metadata(node, url, parent),
                )
            )

    return events
