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


class JsonLdIdentityTest(unittest.TestCase):
    @patch('sources.jsonld.fetch_page_text')
    def test_preserves_identity_metadata_and_original_node(self, fetch):
        import json
        from services.deduplicator import deduplicate_events
        from services.digest import format_event_list
        node = {
            '@type': 'Festival', '@id': '#festival', 'identifier': {'value': '42'},
            'name': 'Festival Ejemplo', 'startDate': '2026-09-12T13:00:00',
            'endDate': '2026-09-12', 'url': 'https://example.com/festival',
            'performer': [{'name': 'Grupo Ejemplo'}], 'organizer': {'name': 'Promotor'},
            'location': {'name': 'CIDE Segovia', 'address': {
                'addressLocality': 'Segovia', 'streetAddress': 'Campos de Castilla',
            }},
            'subEvent': {
                '@type': 'MusicEvent', 'name': 'Grupo Ejemplo',
                'performer': {'name': 'Grupo Ejemplo'}, 'startDate': '2026-09-12T17:15:00',
                'location': {'name': 'CIDE Segovia', 'address': {'addressLocality': 'Segovia'}},
            },
        }
        fetch.return_value = '<script type="application/ld+json">' + json.dumps(node) + '</script>'
        events = extract_events_from_url('https://example.com/page', {date(2026, 9, 12)})
        self.assertEqual(len(events), 2)
        festival, act = events
        self.assertEqual(festival.end_date, date(2026, 9, 12))
        self.assertEqual(festival.external_ids, {'@id': 'https://example.com/page#festival', 'example.com': '42'})
        self.assertEqual(festival.organizer, 'Promotor')
        self.assertEqual(festival.address, 'Campos de Castilla')
        self.assertEqual(festival.participants, ['Grupo Ejemplo'])
        self.assertEqual(festival.original_data, node)
        self.assertEqual(act.parent_event_name, 'Festival Ejemplo')
        self.assertEqual(act.parent_event_url, 'https://example.com/festival')
        result = deduplicate_events(events)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sources[0]['original_data'], node)
        self.assertIn('Festival Ejemplo</b>', format_event_list(result))
        self.assertIn('Incluye: Grupo Ejemplo (17:15)', format_event_list(result))

    @patch('sources.jsonld.fetch_page_text')
    def test_super_event_and_unknown_values(self, fetch):
        fetch.return_value = '''<script type="application/ld+json">{
            "@type":"MusicEvent", "name":"Artista", "startDate":"2026-09-12",
            "superEvent":{"name":"Festival Ejemplo", "url":"/festival"}
        }</script>'''
        event = extract_events_from_url('https://example.com/artist', {date(2026, 9, 12)})[0]
        self.assertEqual(event.parent_event_name, 'Festival Ejemplo')
        self.assertEqual(event.parent_event_url, 'https://example.com/festival')
        self.assertIsNone(event.time)
        self.assertIsNone(event.venue)
        self.assertIsNone(event.municipality)
        self.assertIsNone(event.artist)
        self.assertIsNone(event.end_date)


if __name__ == "__main__":
    unittest.main()
