import unittest
from datetime import date
from unittest.mock import Mock, patch

from sources.jsonld import (
    clear_page_cache,
    extract_events_from_url,
    normalize_schema_type,
)


class JsonLdTest(unittest.TestCase):

    def setUp(self):
        clear_page_cache()

    def tearDown(self):
        clear_page_cache()

    def test_normalizes_schema_prefixed_types(self):
        self.assertEqual(
            normalize_schema_type(
                "schema:SportsEvent"
            ),
            "SportsEvent",
        )

    def test_normalizes_schema_url_types(self):
        self.assertEqual(
            normalize_schema_type(
                "https://schema.org/ExhibitionEvent"
            ),
            "ExhibitionEvent",
        )

    @patch(
        "sources.jsonld.httpx.get"
    )
    def test_extract_events_from_url_reuses_cached_page(
        self,
        http_get_mock,
    ):
        response = Mock()
        response.text = """
            <html>
                <head>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "MusicEvent",
                        "name": "Concierto Cacheado",
                        "startDate": "2026-09-12T21:00:00",
                        "location": {
                            "@type": "Place",
                            "name": "Sala Cache"
                        }
                    }
                    </script>
                </head>
            </html>
        """
        response.raise_for_status.return_value = None
        http_get_mock.return_value = response

        valid_dates = {
            date(
                2026,
                9,
                12,
            )
        }

        first_events = extract_events_from_url(
            "https://example.com/evento",
            valid_dates=valid_dates,
            allowed_types={
                "MusicEvent",
            },
        )

        second_events = extract_events_from_url(
            "https://example.com/evento",
            valid_dates=valid_dates,
            allowed_types={
                "MusicEvent",
            },
        )

        http_get_mock.assert_called_once()

        self.assertEqual(
            first_events[0].title,
            "Concierto Cacheado",
        )

        self.assertEqual(
            second_events[0].title,
            "Concierto Cacheado",
        )


if __name__ == "__main__":
    unittest.main()
