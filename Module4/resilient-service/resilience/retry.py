"""Retry with exponential backoff and full jitter.

Plain exponential backoff synchronises clients: everyone who failed at the same
moment retries at the same moment, and the struggling dependency gets a
thundering herd instead of relief. Full jitter -- a uniform draw from
``[0, cap]`` rather than the cap itself -- spreads the retries out.

``sleep`` and ``rng`` are injected so tests are deterministic and instant.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any


def _always_retryable(exc: BaseException) -> bool:
    return True


class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 2.0,
        retryable: Callable[[BaseException], bool] = _always_retryable,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if max_delay < 0:
            raise ValueError("max_delay must be >= 0")

        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable = retryable
        self._sleep = sleep
        self._rng = rng if rng is not None else random.Random()

        # Set by the caller to feed the retry counter metric.
        self.on_attempt: Callable[[int], None] | None = None

    def delay_for(self, attempt: int) -> float:
        """Jittered delay before the attempt after ``attempt`` (1-based).

        The exponential term is capped at ``max_delay`` *before* the jitter
        draw, so the result is never above the cap and never negative.
        """
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        cap = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        if cap <= 0:
            return 0.0
        return self._rng.uniform(0.0, cap)

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run ``fn``, retrying retryable failures up to ``max_attempts``."""
        last_exc: BaseException | None = None

        for attempt in range(1, self.max_attempts + 1):
            if self.on_attempt is not None:
                self.on_attempt(attempt)
            try:
                return fn(*args, **kwargs)
            except BaseException as exc:
                last_exc = exc
                is_last = attempt == self.max_attempts
                if is_last or not self.retryable(exc):
                    raise
                self._sleep(self.delay_for(attempt))

        # Unreachable: the loop either returns or raises.
        raise last_exc  # pragma: no cover

    def __repr__(self) -> str:
        return (
            f"RetryPolicy(max_attempts={self.max_attempts}, "
            f"base_delay={self.base_delay}, max_delay={self.max_delay})"
        )
