import logging

from html import escape

from config import APP_NAME
from config_locations import CURRENT_LOCATION
from models.location import TargetLocation

from services.dates import get_next_weekend
from services.event_identity import is_festival
from services.event_categories import (
    get_category,
    get_category_commands,
    search_category,
)


WEEKDAY_NAMES = {
    0: "Lun",
    1: "Mar",
    2: "Mié",
    3: "Jue",
    4: "Vie",
    5: "Sáb",
    6: "Dom",
}

logger = logging.getLogger(__name__)


def build_category_digest(
    key: str,
    location: TargetLocation = CURRENT_LOCATION,
) -> str:
    friday, saturday, sunday = get_next_weekend()

    category = get_category(
        key
    )

    events, fallback_results = search_category(
        key,
        location,
    )

    text = (
        f"{category.emoji} <b>{category.title} "
        f"EN {escape(location.name.upper())}</b>\n"
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

        display_name = (
            event.title if is_festival(event)
            else event.artist or event.title
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

        if event.related_events:
            acts = []
            for act in event.related_events:
                label = act.artist or act.title
                if act.time:
                    label += f" ({act.time})"
                acts.append(escape(label))
            text += f"🎶 Incluye: {', '.join(acts)}\n"

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


def build_weekend_digest(
    location: TargetLocation = CURRENT_LOCATION,
) -> str:
    friday, saturday, sunday = (
        get_next_weekend()
    )

    logger.info(
        "Buscando eventos del %s al %s",
        friday,
        sunday,
    )

    text = (
        f"📰 <b>{escape(APP_NAME.upper())}</b>\n"
        f"📍 {escape(location.name)}\n"
        f"📅 {friday.strftime('%d/%m')} "
        f"— {sunday.strftime('%d/%m/%Y')}\n"
    )

    found_anything = False

    for category in get_category_commands():
        events, fallback_results = search_category(
            category.key,
            location,
        )

        if events:
            found_anything = True

            text += (
                f"\n\n{category.emoji} "
                f"<b>{escape(category.title)}</b>"
            )

            text += format_event_list(
                events,
                category.emoji,
            )

            continue

        if fallback_results:
            found_anything = True

            text += (
                f"\n\n{category.emoji} "
                f"<b>{escape(category.title)}</b>\n"
                "No he encontrado eventos con fecha "
                "verificable, pero estos resultados "
                "parecen útiles:"
            )

            text += format_result_list(
                fallback_results[:3]
            )

    if not found_anything:
        text += (
            "\n\nNo he encontrado planes con fecha "
            "verificable para este fin de semana."
        )

    return text
