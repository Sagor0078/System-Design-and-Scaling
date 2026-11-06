"""Circuit breaker behaviour.

Deterministic: a fake clock replaces time.monotonic, so no test sleeps.
"""

import threading

import pytest

from resilience.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def boom():
    raise ValueError("dependency failed")


def test_starts_closed():
    assert CircuitBreaker("t").state is CircuitState.CLOSED


def test_opens_at_failure_threshold():
    cb = CircuitBreaker("t", failure_threshold=3, clock=FakeClock())
    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(boom)
    assert cb.state is CircuitState.OPEN


def test_open_rejects_without_calling_through():
    cb = CircuitBreaker("t", failure_threshold=1, clock=FakeClock())
    with pytest.raises(ValueError):
        cb.call(boom)
    calls = []
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: calls.append(1))
    assert calls == []


def test_success_resets_failure_count():
    cb = CircuitBreaker("t", failure_threshold=2, clock=FakeClock())
    with pytest.raises(ValueError):
        cb.call(boom)
    cb.call(lambda: "ok")
    with pytest.raises(ValueError):
        cb.call(boom)
    assert cb.state is CircuitState.CLOSED


def test_half_open_exactly_at_recovery_timeout():
    clock = FakeClock()
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=10.0, clock=clock)
    with pytest.raises(ValueError):
        cb.call(boom)
    clock.advance(9.999)
    assert cb.state is CircuitState.OPEN
    clock.advance(0.001)
    assert cb.state is CircuitState.HALF_OPEN


def test_zero_recovery_timeout_recovers_immediately():
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=0.0, clock=FakeClock())
    with pytest.raises(ValueError):
        cb.call(boom)
    assert cb.state is CircuitState.HALF_OPEN


def test_half_open_success_closes():
    clock = FakeClock()
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=1.0, clock=clock)
    with pytest.raises(ValueError):
        cb.call(boom)
    clock.advance(1.0)
    assert cb.call(lambda: "ok") == "ok"
    assert cb.state is CircuitState.CLOSED


def test_half_open_failure_reopens_and_restarts_timer():
    clock = FakeClock()
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=1.0, clock=clock)
    with pytest.raises(ValueError):
        cb.call(boom)
    clock.advance(1.0)
    with pytest.raises(ValueError):
        cb.call(boom)
    assert cb.state is CircuitState.OPEN
    clock.advance(0.5)
    assert cb.state is CircuitState.OPEN


def test_half_open_limits_concurrent_probes():
    clock = FakeClock()
    cb = CircuitBreaker(
        "t", failure_threshold=1, recovery_timeout=1.0, half_open_max_calls=1, clock=clock
    )
    with pytest.raises(ValueError):
        cb.call(boom)
    clock.advance(1.0)
    started = threading.Event()
    release = threading.Event()

    def slow():
        started.set()
        release.wait(2)
        return "ok"

    t = threading.Thread(target=lambda: cb.call(slow))
    t.start()
    started.wait(2)
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: "second probe")
    release.set()
    t.join(2)


def test_success_threshold_requires_multiple_probes():
    clock = FakeClock()
    cb = CircuitBreaker(
        "t",
        failure_threshold=1,
        recovery_timeout=1.0,
        half_open_max_calls=2,
        success_threshold=2,
        clock=clock,
    )
    with pytest.raises(ValueError):
        cb.call(boom)
    clock.advance(1.0)
    cb.call(lambda: "ok")
    assert cb.state is CircuitState.HALF_OPEN
    cb.call(lambda: "ok")
    assert cb.state is CircuitState.CLOSED


def test_concurrent_failures_count_once_each():
    cb = CircuitBreaker("t", failure_threshold=50, clock=FakeClock())

    def fail():
        try:
            cb.call(boom)
        except Exception:
            pass

    threads = [threading.Thread(target=fail) for _ in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 40


def test_state_change_callback_fires():
    seen = []
    cb = CircuitBreaker("orders", failure_threshold=1, clock=FakeClock())
    cb.on_state_change = lambda name, state: seen.append((name, state))
    with pytest.raises(ValueError):
        cb.call(boom)
    assert seen == [("orders", CircuitState.OPEN)]
