from dataclasses import dataclass

from config_locations import CURRENT_LOCATION

from models.event import Event

from services.dates import get_next_weekend
from services.deduplicator import deduplicate_events
from services.location_filter import filter_events_by_location
from services.normalizer import (
    normalize_text,
    normalize_venue_name,
)
from services.ranking import rank_events
from services.result_filter import filter_results
from services.source_registry import get_domain
from services.web_search import search_web

from sources.jsonld import extract_events_from_url


PROFESSIONAL_SPORT_TERMS = {
    "real madrid",
    "atletico madrid",
    "atletico de madrid",
    "rayo vallecano",
    "getafe cf",
    "cd leganes",
    "leganes",
    "real madrid femenino",
    "atletico de madrid femenino",
    "madrid cff",
    "movistar estudiantes",
    "estudiantes",
    "baloncesto fuenlabrada",
    "fuenlabrada",
    "inter movistar",
    "movistar inter",
    "alcobendas rugby",
    "complutense cisneros",
    "cr cisneros",
    "club de campo",
    "balonmano alcobendas",
    "laliga",
    "la liga",
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
    "futbol sala",
    "primera division futsal",
    "lnfs",
    "division de honor rugby",
    "liga asobal",
    "superliga voleibol",
    "superliga masculina",
    "superliga femenina",
    "hockey hierba",
    "division de honor hockey",
    "mutua madrid open",
}


PROFESSIONAL_SPORT_VENUES = {
    "santiago bernabeu",
    "riyadh air metropolitano",
    "estadio de vallecas",
    "coliseum",
    "estadio municipal de butarque",
    "movistar arena",
    "palacio vistalegre",
}


PROFESSIONAL_SPORT_CONTEXT_TERMS = {
    "partido",
    "match",
    "jornada",
    "liga",
    "copa",
    "vs",
    "futbol",
    "baloncesto",
    "basket",
    "futbol sala",
    "futsal",
    "rugby",
    "voleibol",
    "balonmano",
    "hockey",
    "tenis",
    "entradas",
}


BLOCKED_PROFESSIONAL_SPORT_DOMAINS = {
    "bing.com",
    "viagogo.com",
    "viagogo.es",
    "stubhub.com",
    "stubhub.es",
    "betfair.es",
    "bet365.es",
    "sportytrader.es",
    "oddschecker.com",
    "apuestasdeportivas.com",
}


@dataclass(frozen=True)
class EventCategory:
    key: str
    command: str
    title: str
    emoji: str
    search_status: str
    category: str
    query_templates: tuple[str, ...]
    allowed_types: set[str]
    max_events_per_day: int = 5
    fallback_results: int = 6


CATEGORIES = {
    "conciertos": EventCategory(
        key="conciertos",
        command="conciertos",
        title="CONCIERTOS",
        emoji="🎤",
        search_status="🎤 Buscando conciertos...",
        category="concert",
        allowed_types={
            "MusicEvent",
        },
        query_templates=(
            "conciertos {location} {dates}",
            "música en directo {location} {dates}",
            "site:livenation.es concierto {location} {dates}",
            "site:ticketmaster.es concierto {location} {dates}",
            "site:songkick.com concert {location} {dates}",
        ),
    ),
    "exposiciones": EventCategory(
        key="exposiciones",
        command="exposiciones",
        title="EXPOSICIONES",
        emoji="🎨",
        search_status="🎨 Buscando exposiciones...",
        category="exhibition",
        allowed_types={
            "Event",
            "ExhibitionEvent",
            "VisualArtsEvent",
        },
        query_templates=(
            "exposiciones {location} {dates}",
            "exposición museo {location} {dates}",
            "agenda exposiciones {location} {dates}",
            "site:madrid.es exposiciones {location} {dates}",
            "site:esmadrid.com exposiciones {location} {dates}",
        ),
    ),
    "ferias": EventCategory(
        key="ferias",
        command="ferias",
        title="FERIAS Y MERCADOS",
        emoji="🎪",
        search_status="🎪 Buscando ferias y mercados...",
        category="fair",
        allowed_types={
            "Event",
            "Festival",
        },
        query_templates=(
            "ferias mercados {location} {dates}",
            "mercadillos {location} {dates}",
            "feria gastronómica {location} {dates}",
            "feria artesanía {location} {dates}",
            "site:madrid.es ferias mercados {location} {dates}",
        ),
    ),
    "fiestas_regionales": EventCategory(
        key="fiestas_regionales",
        command="fiestas_regionales",
        title="FIESTAS REGIONALES",
        emoji="🎉",
        search_status="🎉 Buscando fiestas regionales...",
        category="regional_festival",
        allowed_types={
            "Event",
            "Festival",
        },
        query_templates=(
            "fiestas patronales Comunidad de Madrid {dates}",
            "fiestas populares pueblos Madrid {dates}",
            "fiestas regionales Comunidad de Madrid {dates}",
            "agenda fiestas Comunidad de Madrid {dates}",
        ),
    ),
    "deporte_profesional": EventCategory(
        key="deporte_profesional",
        command="deporte_profesional",
        title="DEPORTE PROFESIONAL",
        emoji="🏟️",
        search_status="🏟️ Buscando deporte profesional...",
        category="professional_sport",
        allowed_types={
            "Event",
            "SportsEvent",
        },
        query_templates=(
            "Real Madrid partido Madrid {dates}",
            "Atlético de Madrid partido Madrid {dates}",
            "Rayo Vallecano partido Madrid {dates}",
            "Getafe CF partido Madrid {dates}",
            "CD Leganés partido Madrid {dates}",
            "Real Madrid baloncesto partido Madrid {dates}",
            "Movistar Estudiantes partido Madrid {dates}",
            "Liga Endesa Madrid partido {dates}",
            "fútbol femenino profesional Madrid partido {dates}",
            "Liga F Madrid partido {dates}",
            "fútbol sala Inter Movistar partido Madrid {dates}",
            "rugby división de honor Madrid partido {dates}",
            "voleibol superliga Madrid partido {dates}",
            "balonmano liga asobal Madrid partido {dates}",
            "hockey hierba división de honor Madrid partido {dates}",
            "tenis profesional Madrid torneo {dates}",
            "site:realmadrid.com entradas partido {dates}",
            "site:atleticodemadrid.com entradas partido {dates}",
            "site:rayovallecano.es entradas partido {dates}",
            "site:getafecf.com entradas partido {dates}",
            "site:cdleganes.com entradas partido {dates}",
        ),
    ),
    "running": EventCategory(
        key="running",
        command="running",
        title="RUNNING POPULAR",
        emoji="🏃",
        search_status="🏃 Buscando carreras populares...",
        category="running",
        allowed_types={
            "Event",
            "SportsEvent",
        },
        query_templates=(
            "carrera popular Madrid {dates}",
            "10K Madrid {dates}",
            "media maratón Madrid {dates}",
            "trail Madrid sierra {dates}",
            "carrera running Comunidad de Madrid {dates}",
        ),
    ),
    "ciclismo": EventCategory(
        key="ciclismo",
        command="ciclismo",
        title="CICLISMO POPULAR",
        emoji="🚴",
        search_status="🚴 Buscando pruebas ciclistas...",
        category="cycling",
        allowed_types={
            "Event",
            "SportsEvent",
        },
        query_templates=(
            "marcha cicloturista Madrid {dates}",
            "carrera ciclismo carretera Madrid {dates}",
            "gravel Madrid evento ciclismo {dates}",
            "XCM BTT Madrid carrera {dates}",
            "MTB Madrid carrera {dates}",
            "ciclismo Comunidad de Madrid {dates}",
        ),
    ),
}


def get_category(
    key: str
) -> EventCategory:
    return CATEGORIES[key]


def get_category_commands() -> list[EventCategory]:
    return list(
        CATEGORIES.values()
    )


def get_date_text() -> str:
    friday, saturday, sunday = get_next_weekend()

    return (
        f"{friday.strftime('%d/%m/%Y')} "
        f"{saturday.strftime('%d/%m/%Y')} "
        f"{sunday.strftime('%d/%m/%Y')}"
    )


def build_queries(
    category: EventCategory
) -> list[str]:
    return [
        template.format(
            location=CURRENT_LOCATION.name,
            dates=get_date_text(),
        )
        for template in category.query_templates
    ]


def discover_urls(
    category: EventCategory
) -> tuple[set[str], list[dict]]:
    urls: set[str] = set()
    search_results: list[dict] = []

    for query in build_queries(
        category
    ):
        print(
            f"{category.emoji} Buscando: {query}"
        )

        try:
            results = search_web(
                query,
                max_results=10,
            )

        except Exception as error:
            print(
                f"⚠️ Error DDGS: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            continue

        search_results.extend(
            results
        )

        for result in results:
            url = result.get("href")

            if (
                url
                and not should_skip_url(
                    category,
                    url,
                )
            ):
                urls.add(url)

    print(
        f"🔗 URLs descubiertas para "
        f"{category.command}: {len(urls)}"
    )

    return urls, search_results


def should_skip_url(
    category: EventCategory,
    url: str,
) -> bool:
    if category.key != "deporte_profesional":
        return False

    domain = get_domain(
        url
    )

    if domain in BLOCKED_PROFESSIONAL_SPORT_DOMAINS:
        print(
            f"🏟️ URL descartada por fuente poco fiable: "
            f"{url}"
        )

        return True

    return False


def extract_category_events(
    category: EventCategory,
    urls: set[str],
) -> list[Event]:
    friday, saturday, sunday = get_next_weekend()

    valid_dates = {
        friday,
        saturday,
        sunday,
    }

    events: list[Event] = []

    for url in urls:
        try:
            page_events = extract_events_from_url(
                url=url,
                valid_dates=valid_dates,
                category=category.category,
                allowed_types=category.allowed_types,
            )

            events.extend(
                page_events
            )

        except Exception as error:
            print(
                f"⚠️ Error procesando {url}: "
                f"{type(error).__name__}: "
                f"{error}"
            )

    print(
        f"{category.emoji} Eventos antes de deduplicar: "
        f"{len(events)}"
    )

    events = filter_events_by_category(
        category,
        events,
    )

    print(
        f"{category.emoji} Eventos tras filtro de categoría: "
        f"{len(events)}"
    )

    events = deduplicate_events(
        events
    )

    print(
        f"{category.emoji} Eventos después de deduplicar: "
        f"{len(events)}"
    )

    events = filter_events_by_location(
        events,
        CURRENT_LOCATION,
    )

    print(
        f"📍 Eventos confirmados en "
        f"{CURRENT_LOCATION.name}: "
        f"{len(events)}"
    )

    events = limit_events_per_day(
        events,
        category.max_events_per_day,
    )

    events.sort(
        key=lambda event: (
            event.date,
            event.time or "99:99",
        )
    )

    print(
        f"{category.emoji} Eventos seleccionados: "
        f"{len(events)}"
    )

    return events


def filter_events_by_category(
    category: EventCategory,
    events: list[Event],
) -> list[Event]:
    if category.key != "deporte_profesional":
        return events

    filtered_events = []

    for event in events:
        if is_professional_sport_event(
            event
        ):
            filtered_events.append(
                event
            )

        else:
            print(
                f"🏟️ Descartado no profesional: "
                f"{event.title} | "
                f"{event.venue} | "
                f"{event.source}"
            )

    return filtered_events


def is_professional_sport_event(
    event: Event
) -> bool:
    haystack = normalize_text(
        " ".join(
            value
            for value in (
                event.title,
                event.artist,
                event.venue,
                event.description,
            )
            if value
        )
    )

    if any(
        term in haystack
        for term in PROFESSIONAL_SPORT_TERMS
    ):
        return True

    venue = normalize_venue_name(
        event.venue
    )

    return (
        venue in PROFESSIONAL_SPORT_VENUES
        and any(
            term in haystack
            for term in PROFESSIONAL_SPORT_CONTEXT_TERMS
        )
    )


def search_category(
    key: str
) -> tuple[list[Event], list[dict]]:
    category = get_category(
        key
    )

    urls, search_results = discover_urls(
        category
    )

    events = extract_category_events(
        category,
        urls,
    )

    fallback_results: list[dict] = []

    if not events:
        fallback_results = filter_results(
            search_results,
            max_results=category.fallback_results,
        )

    return events, fallback_results


def limit_events_per_day(
    events: list[Event],
    per_day: int = 5,
) -> list[Event]:
    events_by_date: dict = {}

    for event in events:
        events_by_date.setdefault(
            event.date,
            []
        ).append(event)

    selected: list[Event] = []

    for day_events in events_by_date.values():
        ranked_events = rank_events(
            day_events
        )

        selected.extend(
            ranked_events[:per_day]
        )

    return selected
