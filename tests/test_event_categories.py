import unittest
from datetime import date

from models.event import Event
from config_locations import get_location
from services.event_categories import (
    CATEGORIES,
    build_queries,
    filter_events_by_category,
    is_professional_sport_event,
    should_skip_url,
)


class EventCategoriesTest(unittest.TestCase):

    def test_expected_categories_are_registered(self):
        self.assertEqual(
            set(CATEGORIES),
            {
                "conciertos",
                "exposiciones",
                "ferias",
                "fiestas_regionales",
                "deporte_profesional",
                "running",
                "ciclismo",
            },
        )

    def test_queries_include_location_and_dates(self):
        queries = build_queries(
            CATEGORIES["running"]
        )

        self.assertTrue(
            any(
                "Comunidad de Madrid" in query
                for query in queries
            )
        )

    def test_queries_can_use_selected_location(self):
        queries = build_queries(
            CATEGORIES["running"],
            get_location("barcelona"),
        )

        self.assertTrue(
            any(
                "Barcelona" in query
                for query in queries
            )
        )

        self.assertFalse(
            any(
                "Madrid" in query
                for query in queries
            )
        )

    def test_professional_sport_keeps_madrid_derby_match(self):
        event = Event(
            title="Real Madrid - Rayo Vallecano",
            category="professional_sport",
            date=date(2026, 9, 12),
            venue="Bernabéu",
        )

        self.assertTrue(
            is_professional_sport_event(
                event
            )
        )

    def test_professional_sport_rejects_social_event(self):
        event = Event(
            title=(
                "La Cordobesa: FREE ENGLISH/ "
                "SPANISH language exchange"
            ),
            category="professional_sport",
            date=date(2026, 9, 11),
            venue="Terraza Collins",
        )

        self.assertFalse(
            is_professional_sport_event(
                event
            )
        )

    def test_professional_sport_rejects_non_match_at_sport_venue(self):
        event = Event(
            title="Concierto de artista ejemplo",
            category="professional_sport",
            date=date(2026, 9, 12),
            venue="Movistar Arena",
        )

        self.assertFalse(
            is_professional_sport_event(
                event
            )
        )

    def test_professional_sport_keeps_futsal_match(self):
        event = Event(
            title="Inter Movistar vs Jimbee Cartagena",
            category="professional_sport",
            date=date(2026, 9, 12),
            venue="Pabellón Jorge Garbajosa",
            description="Partido de Primera División Futsal",
        )

        self.assertTrue(
            is_professional_sport_event(
                event
            )
        )

    def test_professional_sport_keeps_rugby_match(self):
        event = Event(
            title="Alcobendas Rugby vs CR Cisneros",
            category="professional_sport",
            date=date(2026, 9, 13),
            description="División de Honor Rugby",
        )

        self.assertTrue(
            is_professional_sport_event(
                event
            )
        )

    def test_professional_sport_category_filters_noise(self):
        category = CATEGORIES[
            "deporte_profesional"
        ]

        events = [
            Event(
                title="Real Madrid - Rayo Vallecano",
                category="professional_sport",
                date=date(2026, 9, 12),
                venue="Bernabéu",
            ),
            Event(
                title="Young Internationals in Malasaña",
                category="professional_sport",
                date=date(2026, 9, 12),
                venue="Maniquí Bar",
            ),
        ]

        filtered_events = filter_events_by_category(
            category,
            events,
        )

        self.assertEqual(
            filtered_events,
            [
                events[0]
            ],
        )

    def test_professional_sport_skips_resale_and_ad_urls(self):
        category = CATEGORIES[
            "deporte_profesional"
        ]

        self.assertTrue(
            should_skip_url(
                category,
                "https://www.bing.com/aclick?u=example",
            )
        )

        self.assertTrue(
            should_skip_url(
                category,
                "https://www.viagogo.es/Entradas-Deportes",
            )
        )

        self.assertFalse(
            should_skip_url(
                category,
                "https://www.laliga.com/partido/real-madrid-rayo",
            )
        )


if __name__ == "__main__":
    unittest.main()
