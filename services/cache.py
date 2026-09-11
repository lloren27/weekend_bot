from __future__ import annotations

from time import monotonic
from threading import RLock
from typing import Any, Hashable


class TTLCache:
    def __init__(
        self,
        ttl_seconds: int,
    ):
        self.ttl_seconds = ttl_seconds
        self._items: dict[Hashable, tuple[float, Any]] = {}
        self._lock = RLock()

    def get(
        self,
        key: Hashable,
    ) -> Any | None:
        if self.ttl_seconds <= 0:
            return None

        now = monotonic()

        with self._lock:
            item = self._items.get(
                key
            )

            if item is None:
                return None

            expires_at, value = item

            if expires_at <= now:
                self._items.pop(
                    key,
                    None,
                )

                return None

            return value

    def set(
        self,
        key: Hashable,
        value: Any,
    ) -> None:
        if self.ttl_seconds <= 0:
            return

        expires_at = (
            monotonic()
            + self.ttl_seconds
        )

        with self._lock:
            self._items[key] = (
                expires_at,
                value,
            )

    def clear(
        self,
    ) -> None:
        with self._lock:
            self._items.clear()
