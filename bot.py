import os
import asyncio
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import (
    APP_NAME,
    LOG_LEVEL,
)
from config_locations import (
    DEFAULT_LOCATION_KEY,
    find_location_key,
    get_default_location,
    get_location,
    get_location_options,
)
from models.location import TargetLocation
from services.digest import (
    build_weekend_digest,
    build_category_digest,
)
from services.event_categories import (
    get_category_commands,
)


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger = logging.getLogger(__name__)
CHAT_LOCATION_KEY = "location_key"


COMMAND_DESCRIPTIONS = {
    "conciertos": "Conciertos",
    "exposiciones": "Exposiciones",
    "ferias": "Ferias y mercados",
    "fiestas_regionales": "Fiestas regionales",
    "deporte_profesional": "Deporte profesional",
    "running": "Carreras populares",
    "ciclismo": "Pruebas ciclistas",
}


def configure_logging() -> None:
    level = getattr(
        logging,
        LOG_LEVEL.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s: "
            "%(message)s"
        ),
    )


def build_help_text() -> str:
    lines = [
        "👋 Hola.",
        "",
        f"Soy {APP_NAME}.",
        "",
        "Comandos disponibles:",
        "",
        "📍 /ciudad - Ver o cambiar ciudad",
        "🏙️ /ciudades - Ciudades disponibles",
        "📰 /planes - Todos los planes",
    ]

    for category in get_category_commands():
        description = COMMAND_DESCRIPTIONS.get(
            category.command,
            category.title.title(),
        )

        lines.append(
            f"{category.emoji} /{category.command} - {description}"
        )

    lines.extend(
        [
            "❔ /help - Ver todos los comandos",
            "🆔 /id - Ver tu chat_id",
        ]
    )

    return "\n".join(
        lines
    )


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        build_help_text()
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        build_help_text()
    )


async def chat_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        f"Tu chat_id es: {update.effective_chat.id}"
    )


def get_chat_location(
    context: ContextTypes.DEFAULT_TYPE,
) -> TargetLocation:
    location_key = context.chat_data.get(
        CHAT_LOCATION_KEY,
        DEFAULT_LOCATION_KEY,
    )

    try:
        return get_location(
            location_key
        )

    except KeyError:
        context.chat_data[
            CHAT_LOCATION_KEY
        ] = DEFAULT_LOCATION_KEY

        return get_default_location()


def build_location_options_text() -> str:
    names = [
        location.name
        for _, location in get_location_options()
    ]

    return "\n".join(
        f"• {name}"
        for name in names
    )


async def cities(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    current_location = get_chat_location(
        context
    )

    await update.message.reply_text(
        "🏙️ Ciudades disponibles:\n\n"
        f"{build_location_options_text()}\n\n"
        f"Ciudad actual: {current_location.name}\n"
        "Para cambiarla: /ciudad Barcelona"
    )


async def city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    current_location = get_chat_location(
        context
    )

    query = " ".join(
        context.args
    ).strip()

    if not query:
        await update.message.reply_text(
            f"📍 Ciudad actual: {current_location.name}\n\n"
            "Para cambiarla: /ciudad Barcelona\n"
            "Para ver opciones: /ciudades"
        )

        return

    location_key = find_location_key(
        query
    )

    if location_key is None:
        await update.message.reply_text(
            f"No conozco la ciudad \"{query}\".\n\n"
            "Prueba con una de estas:\n"
            f"{build_location_options_text()}"
        )

        return

    context.chat_data[
        CHAT_LOCATION_KEY
    ] = location_key

    location = get_location(
        location_key
    )

    await update.message.reply_text(
        f"✅ Ciudad configurada: {location.name}"
    )


async def planes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    location = get_chat_location(
        context
    )

    status_message = await update.message.reply_text(
        f"🔎 Buscando planes en {location.name} "
        "para este fin de semana..."
    )

    try:
        digest = await asyncio.to_thread(
            build_weekend_digest,
            location,
        )

        chunks = split_message(digest)

        await status_message.edit_text(
            "✅ Planes encontrados"
        )

        for chunk in chunks:
            await update.message.reply_text(
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

    except Exception as error:
        logger.exception(
            "Error buscando eventos: %s: %s",
            type(error).__name__,
            error,
        )

        await status_message.edit_text(
            "❌ Ha ocurrido un error buscando los eventos."
        )


async def concerts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await send_category_digest(
        update,
        context,
        "conciertos",
    )


async def send_category_digest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category_key: str,
):
    category = next(
        category
        for category in get_category_commands()
        if category.key == category_key
    )

    location = get_chat_location(
        context
    )

    status_text = category.search_status.rstrip(
        "."
    )

    status = await update.message.reply_text(
        f"{status_text} en {location.name}..."
    )

    try:
        digest = await asyncio.to_thread(
            build_category_digest,
            category_key,
            location,
        )

        chunks = split_message(
            digest
        )

        await status.delete()

        for chunk in chunks:
            await update.message.reply_text(
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

    except Exception as error:
        logger.exception(
            "Error buscando %s: %s: %s",
            category.command,
            type(error).__name__,
            error,
        )

        await status.edit_text(
            f"❌ Error buscando {category.title.lower()}. "
            "Revisa la terminal para ver el detalle."
        )


def make_category_handler(
    category_key: str
):
    async def handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await send_category_digest(
            update,
            context,
            category_key,
        )

    return handler


def split_message(
    text: str,
    max_length: int = 3900
):
    if len(text) <= max_length:
        return [text]

    chunks = []

    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_at = text.rfind(
            "\n",
            0,
            max_length
        )

        if split_at == -1:
            split_at = max_length

        chunks.append(
            text[:split_at]
        )

        text = text[split_at:].strip()

    return chunks


def main():
    configure_logging()

    if not TOKEN:
        raise RuntimeError(
            "No se ha encontrado "
            "TELEGRAM_BOT_TOKEN en .env"
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "id",
            chat_id
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    app.add_handler(
        CommandHandler(
            "ciudades",
            cities
        )
    )

    app.add_handler(
        CommandHandler(
            "ciudad",
            city
        )
    )

    app.add_handler(
        CommandHandler(
            "planes",
            planes
        )
    )

    app.add_handler(
        CommandHandler(
            "conciertos",
            concerts
        )
    )

    for category in get_category_commands():
        if category.command == "conciertos":
            continue

        app.add_handler(
            CommandHandler(
                category.command,
                make_category_handler(
                    category.key
                )
            )
        )

    logger.info(
        "Bot iniciado"
    )

    app.run_polling()


if __name__ == "__main__":
    main()
