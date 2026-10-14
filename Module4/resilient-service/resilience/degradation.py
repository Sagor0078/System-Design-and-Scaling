"""Graceful degradation through a last-known-good cache.

When the dependency is unreachable there are three honest options: fail, serve
something slightly old, or serve something old and say so. This serves the last
value it saw and labels it stale, so the caller can pass that fact on to its own
caller instead of quietly inventing an answer.

``fallback`` deliberately ignores the TTL -- during an outage, old data beats no
data. A cold cache raises :class:`NoFallbackAvailable` rather than returning an
empty value, because "no stock recorded" and "we cannot reach inventory" must
not look the same to the caller.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class NoFallbackAvailable(RuntimeError):
    """The dependency failed and nothing was cached for this key."""

    def __init__(self, key: str) -> None:
        super().__init__(f"no cached value available for {key!r}")
        self.key = key


@dataclass(frozen=True)
class Fallback:
    """A value plus the provenance the caller needs to be honest about it."""

    value: Any
    stale: bool
    age_seconds: float


class StaleCache:
    def __init__(
        self,
        ttl: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl is not None and ttl < 0:
            raise ValueError("ttl must be >= 0 or None")
        self.ttl = ttl
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[Any, float]] = {}

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            self._entries[key] = (value, self._clock())

    def get_fresh(self, key: str) -> Fallback | None:
        """Return the value only while it is within the TTL, else ``None``."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, stored_at = entry
            age = self._clock() - stored_at
        if self.ttl is not None and age >= self.ttl:
            return None
        return Fallback(value=value, stale=False, age_seconds=age)

    def fallback(self, key: str) -> Fallback:
        """Return the last known value regardless of age, marked stale."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                raise NoFallbackAvailable(key)
            value, stored_at = entry
            age = self._clock() - stored_at
        return Fallback(value=value, stale=True, age_seconds=age)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
