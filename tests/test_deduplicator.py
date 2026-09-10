from datetime import date
import unittest

from models.event import Event
from services.deduplicator import deduplicate_events
from services.normalizer import normalize_venue_name


class DeduplicatorTest(unittest.TestCase):

    def test_merges_commercial_and_popular_venue_names(self):
        events = [
            Event(
                title="Artista Ejemplo",
                artist="Artista Ejemplo",
                category="concert",
                date=date(2026, 9, 12),
                venue="Movistar Arena",
                source_priority=100,
            ),
            Event(
                title="Artista Ejemplo en Madrid",
                artist="Artista Ejemplo",
                category="concert",
                date=date(2026, 9, 12),
                venue="WiZink Center",
                source_priority=85,
            ),
        ]

        self.assertEqual(
            len(deduplicate_events(events)),
            1,
        )

    def test_keeps_same_artist_same_day_in_different_venues(self):
        events = [
            Event(
                title="Artista Ejemplo",
                artist="Artista Ejemplo",
                category="concert",
                date=date(2026, 9, 12),
                venue="La Riviera",
            ),
            Event(
                title="Artista Ejemplo",
                artist="Artista Ejemplo",
                category="concert",
                date=date(2026, 9, 12),
                venue="Teatro Eslava",
            ),
        ]

        self.assertEqual(
            len(deduplicate_events(events)),
            2,
        )

    def test_normalizes_known_venue_aliases(self):
        self.assertEqual(
            normalize_venue_name(
                "Palacio de los Deportes de Madrid"
            ),
            normalize_venue_name(
                "WiZink Center"
            ),
        )

    def test_merges_professional_match_with_reversed_teams(self):
        events = [
            Event(
                title="Rayo Vallecano, Real Madrid",
                artist="Rayo Vallecano, Real Madrid",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="19:00",
                venue="Bernabéu",
                source_priority=60,
            ),
            Event(
                title="Real Madrid, Rayo Vallecano",
                artist="Real Madrid, Rayo Vallecano",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="19:00",
                venue="Estadio Bernabéu",
                source_priority=90,
            ),
        ]

        self.assertEqual(
            len(deduplicate_events(events)),
            1,
        )

    def test_merges_professional_match_with_team_aliases(self):
        events = [
            Event(
                title="RC Deportivo, Getafe CF",
                artist="RC Deportivo, Getafe CF",
                category="professional_sport",
                date=date(2026, 9, 13),
                time="16:30",
                venue="Coliseum",
            ),
            Event(
                title="Getafe vs Deportivo",
                artist="Getafe vs Deportivo",
                category="professional_sport",
                date=date(2026, 9, 13),
                time="16:30",
                venue="Estadio Coliseum",
            ),
        ]

        self.assertEqual(
            len(deduplicate_events(events)),
            1,
        )

    def test_merges_professional_match_with_competition_and_time_offset(self):
        events = [
            Event(
                title="Real Madrid, Rayo Vallecano",
                artist="Real Madrid, Rayo Vallecano",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="19:00",
                venue="Estadio Bernabéu",
                source_priority=95,
            ),
            Event(
                title="Real Madrid, Rayo Vallecano",
                artist="Real Madrid, Rayo Vallecano",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="21:00",
                venue="Santiago Bernabeu",
                price="83.66 €",
                source_priority=40,
            ),
            Event(
                title="Real Madrid, La Liga, Rayo Vallecano",
                artist="Real Madrid, La Liga, Rayo Vallecano",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="21:00",
                venue="Estadio Santiago Bernabeu",
                price="136 USD",
                source_priority=40,
            ),
        ]

        unique_events = deduplicate_events(
            events
        )

        self.assertEqual(
            len(unique_events),
            1,
        )

        self.assertEqual(
            unique_events[0].time,
            "19:00",
        )

        self.assertEqual(
            unique_events[0].artist,
            "Real Madrid - Rayo Vallecano",
        )

    def test_merges_professional_match_with_at_separator(self):
        events = [
            Event(
                title="Real Madrid - Rayo Vallecano",
                artist="Real Madrid - Rayo Vallecano",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="19:00",
                venue="Bernabéu",
                source_priority=95,
            ),
            Event(
                title="Rayo @ Real Madrid",
                artist="Rayo @ Real Madrid",
                category="professional_sport",
                date=date(2026, 9, 12),
                time="20:00",
                venue="Estadio Bernabéu",
                source_priority=60,
            ),
        ]

        unique_events = deduplicate_events(
            events
        )

        self.assertEqual(
            len(unique_events),
            1,
        )

        self.assertEqual(
            unique_events[0].artist,
            "Real Madrid - Rayo Vallecano",
        )

    def test_professional_match_display_uses_home_team_from_venue(self):
        events = [
            Event(
                title="RC Deportivo, Getafe CF",
                artist="RC Deportivo, Getafe CF",
                category="professional_sport",
                date=date(2026, 9, 13),
                time="16:30",
                venue="Coliseum",
            )
        ]

        unique_events = deduplicate_events(
            events
        )

        self.assertEqual(
            unique_events[0].artist,
            "Getafe CF - RC Deportivo",
        )


if __name__ == "__main__":
    unittest.main()
