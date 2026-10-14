"""A circuit breaker.

Three states. CLOSED lets calls through and counts consecutive failures. At
``failure_threshold`` consecutive failures it moves to OPEN, where calls are
rejected immediately with :class:`CircuitOpenError` -- the dependency gets a
rest and the caller gets a fast failure instead of a pile-up of timeouts. After
``recovery_timeout`` seconds it moves to HALF_OPEN and admits at most
``half_open_max_calls`` probe calls at a time: ``success_threshold`` successes
close it, a single failure sends it back to OPEN and restarts the timer.

The clock is injected so the behaviour is testable without sleeping, and every
state read and mutation is under one lock so concurrent callers cannot lose a
transition or double-count a failure.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised instead of calling through when the circuit is open."""

    def __init__(self, name: str, retry_after: float) -> None:
        super().__init__(f"circuit {name!r} is open; retry in {retry_after:.2f}s")
        self.name = name
        self.retry_after = retry_after


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 10.0,
        half_open_max_calls: int = 1,
        success_threshold: int = 1,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout < 0:
            raise ValueError("recovery_timeout must be >= 0")
        if half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")
        if success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")

        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self._clock = clock

        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self.failure_count = 0
        self._opened_at = 0.0
        self._half_open_in_flight = 0
        self._half_open_successes = 0

        # Set by the caller to feed the Prometheus gauge. Invoked outside the
        # lock so a slow callback cannot stall request handling.
        self.on_state_change: Callable[[str, CircuitState], None] | None = None

    # ------------------------------------------------------------------ state

    @property
    def state(self) -> CircuitState:
        with self._lock:
            transition = self._maybe_half_open()
        self._notify(transition)
        return self._state

    def _maybe_half_open(self) -> CircuitState | None:
        """Promote OPEN -> HALF_OPEN once the recovery window has elapsed.

        Called with the lock held. The comparison is ``>=`` so a breaker with a
        zero recovery timeout is immediately probeable, and one at exactly
        ``recovery_timeout`` seconds does not wait an extra tick.
        """
        if self._state is not CircuitState.OPEN:
            return None
        if self._clock() - self._opened_at < self.recovery_timeout:
            return None
        self._state = CircuitState.HALF_OPEN
        self._half_open_in_flight = 0
        self._half_open_successes = 0
        return CircuitState.HALF_OPEN

    def _notify(self, transition: CircuitState | None) -> None:
        if transition is not None and self.on_state_change is not None:
            self.on_state_change(self.name, transition)

    def _retry_after(self) -> float:
        return max(0.0, self.recovery_timeout - (self._clock() - self._opened_at))

    # ------------------------------------------------------------------- call

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run ``fn`` through the breaker, or reject it without calling."""
        is_probe = self._acquire()
        try:
            result = fn(*args, **kwargs)
        except BaseException:
            self._record_failure(is_probe)
            raise
        self._record_success(is_probe)
        return result

    def _acquire(self) -> bool:
        """Reserve the right to call through. Returns True for a probe call."""
        with self._lock:
            transition = self._maybe_half_open()
            state = self._state

            if state is CircuitState.OPEN:
                error = CircuitOpenError(self.name, self._retry_after())
                self._notify(transition)
                raise error

            if state is CircuitState.HALF_OPEN:
                if self._half_open_in_flight >= self.half_open_max_calls:
                    error = CircuitOpenError(self.name, 0.0)
                    self._notify(transition)
                    raise error
                self._half_open_in_flight += 1
                self._notify(transition)
                return True

        self._notify(transition)
        return False

    def _record_success(self, is_probe: bool) -> None:
        with self._lock:
            if is_probe:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._half_open_successes += 1
                if self._half_open_successes >= self.success_threshold:
                    transition = self._close()
                else:
                    transition = None
            else:
                self.failure_count = 0
                transition = None
        self._notify(transition)

    def _record_failure(self, is_probe: bool) -> None:
        with self._lock:
            if is_probe:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                transition = self._open()
            else:
                self.failure_count += 1
                transition = (
                    self._open() if self.failure_count >= self.failure_threshold else None
                )
        self._notify(transition)

    def _open(self) -> CircuitState:
        self._state = CircuitState.OPEN
        self._opened_at = self._clock()
        self._half_open_successes = 0
        return CircuitState.OPEN

    def _close(self) -> CircuitState:
        self._state = CircuitState.CLOSED
        self.failure_count = 0
        self._half_open_successes = 0
        self._half_open_in_flight = 0
        return CircuitState.CLOSED

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, state={self._state.value!r}, "
            f"failures={self.failure_count})"
        )
