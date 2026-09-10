import os
import asyncio

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import APP_NAME
from services.digest import (
    build_weekend_digest,
    build_category_digest,
)
from services.event_categories import (
    get_category_commands,
)


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


COMMAND_DESCRIPTIONS = {
    "conciertos": "Conciertos",
    "exposiciones": "Exposiciones",
    "ferias": "Ferias y mercados",
    "fiestas_regionales": "Fiestas regionales",
    "deporte_profesional": "Deporte profesional",
    "running": "Carreras populares",
    "ciclismo": "Pruebas ciclistas",
}


def build_help_text() -> str:
    lines = [
        "👋 Hola.",
        "",
        f"Soy {APP_NAME}.",
        "",
        "Comandos disponibles:",
        "",
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


async def planes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    status_message = await update.message.reply_text(
        "🔎 Buscando planes para este fin de semana..."
    )

    try:
        digest = await asyncio.to_thread(
            build_weekend_digest
        )

        chunks = split_message(digest)

        await status_message.edit_text(
            "✅ Planes encontrados"
        )

        for chunk in chunks:
            await update.message.reply_text(
                chunk,
                disable_web_page_preview=True
            )

    except Exception as error:
        print(
            f"❌ Error buscando eventos: "
            f"{type(error).__name__}: {error}"
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
        "conciertos",
    )


async def send_category_digest(
    update: Update,
    category_key: str,
):
    category = next(
        category
        for category in get_category_commands()
        if category.key == category_key
    )

    status = await update.message.reply_text(
        category.search_status
    )

    try:
        digest = await asyncio.to_thread(
            build_category_digest,
            category_key,
        )

        # Protección frente al límite de Telegram.
        if len(digest) > 4000:
            raise ValueError(
                f"El digest de {category.command} es demasiado largo: "
                f"{len(digest)} caracteres"
            )

        await status.delete()

        await update.message.reply_text(
            digest,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as error:
        print(
            f"❌ Error buscando {category.command}: "
            f"{type(error).__name__}: {error}"
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

    print("🤖 Bot iniciado...")

    app.run_polling()


if __name__ == "__main__":
    main()
