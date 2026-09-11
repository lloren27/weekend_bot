import unittest
from unittest.mock import patch

from services.cache import TTLCache


class TTLCacheTest(unittest.TestCase):

    def test_cache_returns_value_before_expiry(self):
        cache = TTLCache(
            ttl_seconds=30
        )

        with patch(
            "services.cache.monotonic",
            return_value=100,
        ):
            cache.set(
                "key",
                "value",
            )

        with patch(
            "services.cache.monotonic",
            return_value=120,
        ):
            self.assertEqual(
                cache.get("key"),
                "value",
            )

    def test_cache_expires_values(self):
        cache = TTLCache(
            ttl_seconds=30
        )

        with patch(
            "services.cache.monotonic",
            return_value=100,
        ):
            cache.set(
                "key",
                "value",
            )

        with patch(
            "services.cache.monotonic",
            return_value=131,
        ):
            self.assertIsNone(
                cache.get("key")
            )

    def test_cache_can_be_disabled_with_zero_ttl(self):
        cache = TTLCache(
            ttl_seconds=0
        )

        cache.set(
            "key",
            "value",
        )

        self.assertIsNone(
            cache.get("key")
        )


if __name__ == "__main__":
    unittest.main()
