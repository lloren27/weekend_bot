from datetime import date
import unittest

from config_locations import CURRENT_LOCATION
from models.event import Event
from services.location_filter import matches_location


class LocationFilterTest(unittest.TestCase):

    def test_known_madrid_venue_matches_without_address(self):
        event = Event(
            title="Real Madrid - Rayo Vallecano",
            category="professional_sport",
            date=date(2026, 9, 12),
            venue="Bernabéu",
        )

        self.assertTrue(
            matches_location(
                event,
                CURRENT_LOCATION,
            )
        )

    def test_unknown_venue_without_address_does_not_match(self):
        event = Event(
            title="Sevilla FC - Valencia CF",
            category="professional_sport",
            date=date(2026, 9, 12),
            venue="Ramón Sánchez-Pizjuán",
        )

        self.assertFalse(
            matches_location(
                event,
                CURRENT_LOCATION,
            )
        )

    def test_estadio_fernando_torres_matches_without_address(self):
        event = Event(
            title="Madrid CFF - Sevilla FC",
            category="professional_sport",
            date=date(2026, 9, 12),
            venue="Estadio Fernando Torres",
        )

        self.assertTrue(
            matches_location(
                event,
                CURRENT_LOCATION,
            )
        )


if __name__ == "__main__":
    unittest.main()
