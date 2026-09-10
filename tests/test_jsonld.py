import unittest

from sources.jsonld import normalize_schema_type


class JsonLdTest(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
