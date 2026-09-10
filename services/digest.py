from html import escape

from config import APP_NAME
from config_locations import CURRENT_LOCATION

from services.dates import get_next_weekend
from services.event_categories import (
    get_category,
    search_category,
)
from services.search import search_weekend_events


WEEKDAY_NAMES = {
    0: "Lun",
    1: "Mar",
    2: "Mié",
    3: "Jue",
    4: "Vie",
    5: "Sáb",
    6: "Dom",
}


def build_category_digest(
    key: str
) -> str:
    friday, saturday, sunday = get_next_weekend()

    category = get_category(
        key
    )

    events, fallback_results = search_category(
        key
    )

    text = (
        f"{category.emoji} <b>{category.title} "
        f"EN {escape(CURRENT_LOCATION.name.upper())}</b>\n"
        f"📅 {friday.strftime('%d/%m')} "
        f"— {sunday.strftime('%d/%m/%Y')}\n"
    )

    if events:
        return (
            text
            + format_event_list(
                events,
                category.emoji,
            )
        )

    if fallback_results:
        return (
            text
            + "\nNo he encontrado eventos con fecha "
            "verificable, pero estos resultados parecen "
            "útiles:\n"
            + format_result_list(
                fallback_results
            )
        )

    return (
        text
        + "\nNo he encontrado planes con fecha "
        "verificable para este fin de semana."
    )


def build_concert_digest():
    return build_category_digest(
        "conciertos"
    )


def format_event_list(
    events,
    icon: str = "🎵",
) -> str:
    text = ""
    for event in events:
        if not event.date:
            continue

        # Si conocemos el artista, mostramos el artista.
        # Si no, utilizamos el título del evento.
        display_name = (
            event.artist
            or event.title
        )

        weekday = WEEKDAY_NAMES[
            event.date.weekday()
        ]

        date_line = (
            f"{weekday} "
            f"{event.date.day}"
        )

        if event.time:
            date_line += (
                f" · {event.time}"
            )

        text += (
            f"\n\n{icon} <b>{escape(display_name)}</b>\n"
            f"📅 {date_line}\n"
        )

        if event.venue:
            text += (
                f"📍 {escape(event.venue)}\n"
            )

        if event.free:
            text += "🆓 Gratis\n"

        elif (
            event.price
            and event.category != "professional_sport"
        ):
            text += (
                f"💰 {escape(event.price)}\n"
            )

        if event.sold_out:
            text += (
                "🔴 Entradas agotadas\n"
            )

        if event.url:
            safe_url = escape(
                event.url,
                quote=True
            )

            text += (
                f'<a href="{safe_url}">'
                f'🔗 Ver evento'
                f'</a>\n'
            )

    return text


def format_result_list(
    results: list[dict]
) -> str:
    text = ""

    for result in results:
        title = escape(
            result.get(
                "title",
                "Evento",
            )
        )

        body = escape(
            clean_text(
                result.get(
                    "body",
                    ""
                ),
                max_length=160,
            )
        )

        url = result.get(
            "href",
            ""
        )

        text += (
            f"\n\n• <b>{title}</b>\n"
        )

        if body:
            text += (
                f"{body}\n"
            )

        if url:
            safe_url = escape(
                url,
                quote=True,
            )

            text += (
                f'<a href="{safe_url}">'
                f'🔗 Ver resultado'
                f'</a>\n'
            )

    return text


def clean_text(
    text: str,
    max_length: int = 100
):
    if not text:
        return ""

    text = (
        text
        .replace("\n", " ")
        .strip()
    )

    if len(text) > max_length:
        return (
            text[:max_length - 3]
            + "..."
        )

    return text


def build_weekend_digest():
    friday, saturday, sunday = (
        get_next_weekend()
    )

    print(
        f"🔎 Buscando eventos "
        f"del {friday} al {sunday}"
    )

    events = search_weekend_events()

    text = (
        f"📰 {APP_NAME.upper()}\n"
        f"📍 {CURRENT_LOCATION.name}\n"
        f"📅 {friday.strftime('%d/%m')} "
        f"— {sunday.strftime('%d/%m/%Y')}\n"
    )

    for category, results in events.items():
        if not results:
            continue

        text += (
            f"\n\n{category}\n"
        )

        for result in results:
            title = result.get(
                "title",
                "Evento"
            )

            body = clean_text(
                result.get(
                    "body",
                    ""
                )
            )

            url = result.get(
                "href",
                ""
            )

            text += (
                f"\n• {title}\n"
            )

            if body:
                text += (
                    f"{body}\n"
                )

            if url:
                text += (
                    f"🔗 {url}\n"
                )

    return text
