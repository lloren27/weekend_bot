import unittest
from unittest.mock import patch
from datetime import date

from models.event import Event
from config_locations import CURRENT_LOCATION
from services.digest import (
    build_category_digest,
    build_weekend_digest,
    format_event_list,
)
from services.event_categories import EventCategory


class DigestTest(unittest.TestCase):

    def make_category(
        self,
        key: str,
        title: str,
        emoji: str,
    ) -> EventCategory:
        return EventCategory(
            key=key,
            command=key,
            title=title,
            emoji=emoji,
            search_status=f"{emoji} Buscando...",
            category=key,
            query_templates=(),
            allowed_types={
                "Event",
            },
        )

    @patch(
        "services.digest.search_category"
    )
    def test_category_digest_formats_fallback_results(
        self,
        search_category_mock,
    ):
        search_category_mock.return_value = (
            [],
            [
                {
                    "title": "Carrera Popular Centro",
                    "body": "Inscripciones abiertas.",
                    "href": "https://example.com/carrera",
                }
            ],
        )

        text = build_category_digest(
            "running"
        )

        self.assertIn(
            "RUNNING POPULAR",
            text,
        )

        self.assertIn(
            "Carrera Popular Centro",
            text,
        )

        self.assertIn(
            "https://example.com/carrera",
            text,
        )

    def test_professional_sport_event_list_hides_price(self):
        text = format_event_list(
            [
                Event(
                    title="Real Madrid - Rayo Vallecano",
                    category="professional_sport",
                    date=date(2026, 9, 12),
                    time="19:00",
                    venue="Bernabéu",
                    price="135 USD",
                )
            ],
            icon="🏟️",
        )

        self.assertNotIn(
            "135 USD",
            text,
        )

    @patch(
        "services.digest.get_category_commands"
    )
    @patch(
        "services.digest.search_category"
    )
    def test_weekend_digest_uses_category_pipeline(
        self,
        search_category_mock,
        get_category_commands_mock,
    ):
        get_category_commands_mock.return_value = [
            self.make_category(
                "conciertos",
                "CONCIERTOS",
                "🎤",
            ),
        ]

        search_category_mock.return_value = (
            [
                Event(
                    title="Noche de jazz",
                    category="concert",
                    date=date(2026, 9, 12),
                    time="21:00",
                    venue="Sala Central",
                    url="https://example.com/jazz",
                )
            ],
            [],
        )

        text = build_weekend_digest()

        search_category_mock.assert_called_once_with(
            "conciertos",
            CURRENT_LOCATION,
        )

        self.assertIn(
            "<b>CONCIERTOS</b>",
            text,
        )

        self.assertIn(
            "Noche de jazz",
            text,
        )

        self.assertIn(
            "Sala Central",
            text,
        )

    @patch(
        "services.digest.get_category_commands"
    )
    @patch(
        "services.digest.search_category"
    )
    def test_weekend_digest_formats_category_fallback(
        self,
        search_category_mock,
        get_category_commands_mock,
    ):
        get_category_commands_mock.return_value = [
            self.make_category(
                "running",
                "RUNNING POPULAR",
                "🏃",
            ),
        ]

        search_category_mock.return_value = (
            [],
            [
                {
                    "title": "Carrera Popular Centro",
                    "body": "Inscripciones abiertas.",
                    "href": "https://example.com/carrera",
                }
            ],
        )

        text = build_weekend_digest()

        self.assertIn(
            "RUNNING POPULAR",
            text,
        )

        self.assertIn(
            "No he encontrado eventos con fecha verificable",
            text,
        )

        self.assertIn(
            "Carrera Popular Centro",
            text,
        )


if __name__ == "__main__":
    unittest.main()
