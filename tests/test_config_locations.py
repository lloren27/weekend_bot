import unittest

from config_locations import (
    CURRENT_LOCATION,
    find_location,
    find_location_key,
    get_location,
    get_location_options,
)


class ConfigLocationsTest(unittest.TestCase):

    def test_default_location_remains_comunidad_de_madrid(self):
        self.assertEqual(
            CURRENT_LOCATION.name,
            "Comunidad de Madrid",
        )

    def test_find_location_accepts_accentless_aliases(self):
        self.assertEqual(
            find_location_key("Cordoba"),
            "cordoba",
        )

        self.assertEqual(
            find_location("bcn"),
            get_location("barcelona"),
        )

    def test_location_options_include_major_spanish_cities(self):
        names = {
            location.name
            for _, location in get_location_options()
        }

        self.assertIn(
            "Barcelona",
            names,
        )

        self.assertIn(
            "Valencia",
            names,
        )

        self.assertIn(
            "Sevilla",
            names,
        )


if __name__ == "__main__":
    unittest.main()
