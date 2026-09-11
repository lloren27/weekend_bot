import unittest
from unittest.mock import AsyncMock, Mock, patch

from bot import (
    build_help_text,
    city,
    cities,
    get_chat_location,
    send_category_digest,
    split_message,
)
from config_locations import (
    CURRENT_LOCATION,
    get_location,
)
from services.event_categories import EventCategory


class BotHelpTest(unittest.TestCase):

    def test_help_text_includes_all_commands(self):
        text = build_help_text()

        for command in (
            "/planes",
            "/ciudad",
            "/ciudades",
            "/conciertos",
            "/exposiciones",
            "/ferias",
            "/fiestas_regionales",
            "/deporte_profesional",
            "/running",
            "/ciclismo",
            "/help",
            "/id",
        ):
            self.assertIn(
                command,
                text,
            )


class BotMessageTest(unittest.TestCase):

    def test_split_message_breaks_long_text_on_newlines(self):
        text = "\n".join(
            f"Línea {index}"
            for index in range(20)
        )

        chunks = split_message(
            text,
            max_length=40,
        )

        self.assertGreater(
            len(chunks),
            1,
        )

        self.assertTrue(
            all(
                len(chunk) <= 40
                for chunk in chunks
            )
        )


class BotCategoryDigestTest(unittest.IsolatedAsyncioTestCase):

    @patch(
        "bot.build_category_digest"
    )
    @patch(
        "bot.get_category_commands"
    )
    async def test_category_digest_sends_long_text_in_chunks(
        self,
        get_category_commands_mock,
        build_category_digest_mock,
    ):
        category = EventCategory(
            key="conciertos",
            command="conciertos",
            title="CONCIERTOS",
            emoji="🎤",
            search_status="🎤 Buscando conciertos...",
            category="concert",
            query_templates=(),
            allowed_types={
                "MusicEvent",
            },
        )

        get_category_commands_mock.return_value = [
            category
        ]

        digest = "\n".join(
            f"<b>Evento {index}</b>"
            for index in range(500)
        )

        expected_chunks = split_message(
            digest
        )

        build_category_digest_mock.return_value = digest

        status = Mock()
        status.delete = AsyncMock()
        status.edit_text = AsyncMock()

        update = Mock()
        update.message.reply_text = AsyncMock(
            return_value=status
        )

        context = Mock()
        context.chat_data = {}

        await send_category_digest(
            update,
            context,
            "conciertos",
        )

        build_category_digest_mock.assert_called_once_with(
            "conciertos",
            CURRENT_LOCATION,
        )

        status.delete.assert_awaited_once()
        status.edit_text.assert_not_awaited()

        self.assertEqual(
            update.message.reply_text.await_count,
            1 + len(expected_chunks),
        )

        sent_chunks = [
            call.kwargs
            for call in update.message.reply_text.await_args_list[1:]
        ]

        self.assertTrue(
            all(
                call["parse_mode"] == "HTML"
                for call in sent_chunks
            )
        )

        self.assertEqual(
            [
                call.args[0]
                for call in update.message.reply_text.await_args_list[1:]
            ],
            expected_chunks,
        )


class BotLocationTest(unittest.IsolatedAsyncioTestCase):

    async def test_city_without_args_shows_current_location(self):
        update = Mock()
        update.message.reply_text = AsyncMock()

        context = Mock()
        context.args = []
        context.chat_data = {}

        await city(
            update,
            context,
        )

        reply = update.message.reply_text.await_args.args[0]

        self.assertIn(
            "Comunidad de Madrid",
            reply,
        )

        self.assertIn(
            "/ciudades",
            reply,
        )

    async def test_city_sets_chat_location_from_alias(self):
        update = Mock()
        update.message.reply_text = AsyncMock()

        context = Mock()
        context.args = [
            "bcn"
        ]
        context.chat_data = {}

        await city(
            update,
            context,
        )

        self.assertEqual(
            get_chat_location(context),
            get_location("barcelona"),
        )

        reply = update.message.reply_text.await_args.args[0]

        self.assertIn(
            "Barcelona",
            reply,
        )

    async def test_city_rejects_unknown_location(self):
        update = Mock()
        update.message.reply_text = AsyncMock()

        context = Mock()
        context.args = [
            "Atlantis"
        ]
        context.chat_data = {}

        await city(
            update,
            context,
        )

        self.assertEqual(
            get_chat_location(context),
            CURRENT_LOCATION,
        )

        reply = update.message.reply_text.await_args.args[0]

        self.assertIn(
            "No conozco",
            reply,
        )

    async def test_cities_lists_options(self):
        update = Mock()
        update.message.reply_text = AsyncMock()

        context = Mock()
        context.chat_data = {
            "location_key": "valencia"
        }

        await cities(
            update,
            context,
        )

        reply = update.message.reply_text.await_args.args[0]

        self.assertIn(
            "Barcelona",
            reply,
        )

        self.assertIn(
            "Valencia",
            reply,
        )


if __name__ == "__main__":
    unittest.main()
