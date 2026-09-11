import unittest
from unittest.mock import MagicMock, patch

from services.web_search import (
    clear_search_cache,
    search_web,
)


class WebSearchTest(unittest.TestCase):

    def setUp(self):
        clear_search_cache()

    def tearDown(self):
        clear_search_cache()

    @patch(
        "services.web_search.DDGS"
    )
    def test_search_web_reuses_cached_results(
        self,
        ddgs_mock,
    ):
        ddgs_context = MagicMock()
        ddgs_mock.return_value = ddgs_context

        ddgs = ddgs_context.__enter__.return_value
        ddgs.text.return_value = [
            {
                "title": "Plan",
                "href": "https://example.com",
            }
        ]

        first_results = search_web(
            "planes Madrid",
            max_results=3,
        )

        first_results[0]["title"] = "Mutado"

        second_results = search_web(
            "planes Madrid",
            max_results=3,
        )

        ddgs.text.assert_called_once_with(
            "planes Madrid",
            region="es-es",
            max_results=3,
        )

        self.assertEqual(
            second_results[0]["title"],
            "Plan",
        )

    @patch(
        "services.web_search.DDGS"
    )
    def test_search_web_cache_key_includes_max_results(
        self,
        ddgs_mock,
    ):
        ddgs_context = MagicMock()
        ddgs_mock.return_value = ddgs_context

        ddgs = ddgs_context.__enter__.return_value
        ddgs.text.return_value = []

        search_web(
            "planes Madrid",
            max_results=3,
        )

        search_web(
            "planes Madrid",
            max_results=5,
        )

        self.assertEqual(
            ddgs.text.call_count,
            2,
        )


if __name__ == "__main__":
    unittest.main()
