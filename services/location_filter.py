import logging

from models.event import Event
from models.location import TargetLocation

from services.normalizer import (
    normalize_text,
    normalize_venue_name,
)


COUNTRY_ALIASES = {
    "es": "espana",
    "esp": "espana",
    "espana": "espana",
    "spain": "espana",
}


COMMUNITY_OF_MADRID_VENUES = {
    "santiago bernabeu",
    "riyadh air metropolitano",
    "estadio de vallecas",
    "coliseum",
    "estadio municipal de butarque",
    "estadio fernando torres",
    "movistar arena",
    "palacio vistalegre",
}

logger = logging.getLogger(__name__)


def normalize_country(
    value: str | None
) -> str:
    normalized = normalize_text(
        value
    )

    if not normalized:
        return ""

    return COUNTRY_ALIASES.get(
        normalized,
        normalized,
    )


def normalize_values(
    values: set[str]
) -> set[str]:
    return {
        normalized
        for value in values
        if (
            normalized := normalize_text(
                value
            )
        )
    }


def matches_location(
    event: Event,
    target: TargetLocation,
) -> bool:

    event_country = normalize_country(
        event.country
    )

    target_country = normalize_country(
        target.country
    )

    event_region = normalize_text(
        event.region
    )

    event_municipality = normalize_text(
        event.municipality
    )

    postal_code = normalize_text(
        event.postal_code
    )

    event_venue = normalize_venue_name(
        event.venue
    )

    target_regions = normalize_values(
        target.regions
    )

    target_municipalities = normalize_values(
        target.municipalities
    )

    target_postal_prefixes = {
        str(prefix).strip()
        for prefix in target.postal_prefixes
        if str(prefix).strip()
    }

    # ==================================
    # 1. PAÍS
    # ==================================
    #
    # Solo descartamos si conocemos ambos
    # países y son claramente diferentes.

    if (
        event_country
        and target_country
        and event_country != target_country
    ):
        return False

    # ==================================
    # 2. RECINTO CONOCIDO
    # ==================================
    #
    # Algunas fuentes de deporte devuelven
    # solo "Bernabéu" o "Coliseum" sin
    # dirección. En esos casos el recinto
    # conocido confirma Madrid.

    if (
        event_venue
        and event_venue in COMMUNITY_OF_MADRID_VENUES
    ):
        target_region_names = normalize_values(
            {
                target.name,
                *target.regions,
            }
        )

        if (
            "madrid" in target_region_names
            or "comunidad de madrid"
            in target_region_names
            or "28" in target_postal_prefixes
        ):
            return True

    # ==================================
    # 3. CÓDIGO POSTAL
    # ==================================

    if (
        postal_code
        and target_postal_prefixes
    ):
        if any(
            postal_code.startswith(prefix)
            for prefix in target_postal_prefixes
        ):
            return True

    # ==================================
    # 4. REGIÓN
    # ==================================

    if (
        event_region
        and target_regions
        and event_region in target_regions
    ):
        return True

    # ==================================
    # 5. MUNICIPIO
    # ==================================

    if (
        event_municipality
        and target_municipalities
        and event_municipality
        in target_municipalities
    ):
        return True

    # ==================================
    # 6. MUNICIPIO COINCIDE CON REGIÓN
    # ==================================
    #
    # Hay fuentes que devuelven, por ejemplo:
    #
    # municipality = Madrid
    # region       = Madrid
    #
    # o incluso solo municipality = Madrid.

    if (
        event_municipality
        and target_regions
        and event_municipality in target_regions
    ):
        return True

    # ==================================
    # 7. TARGET = PAÍS COMPLETO
    # ==================================

    has_geographic_restrictions = any(
        (
            target_regions,
            target_municipalities,
            target_postal_prefixes,
        )
    )

    if not has_geographic_restrictions:

        # Si conocemos el país,
        # tiene que coincidir.

        if event_country:
            return (
                event_country
                == target_country
            )

        # Si la fuente no informa del país,
        # no podemos demostrar que esté fuera.
        return True

    return False


def filter_events_by_location(
    events: list[Event],
    target: TargetLocation,
) -> list[Event]:

    valid_events = []

    for event in events:

        if matches_location(
            event,
            target,
        ):
            valid_events.append(
                event
            )

        else:
            logger.debug(
                "Fuera de %s: %s | %s | %s | %s | %s | %s",
                target.name,
                event.title,
                event.venue,
                event.municipality,
                event.region,
                event.country,
                event.postal_code,
            )

    return valid_events
