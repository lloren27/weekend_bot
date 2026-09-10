import unittest
from unittest.mock import patch
from datetime import date

from models.event import Event
from services.digest import build_category_digest
from services.digest import format_event_list


class DigestTest(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
