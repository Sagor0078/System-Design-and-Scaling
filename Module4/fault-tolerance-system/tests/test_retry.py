"""Retry policy behaviour.

Deterministic: sleep is recorded rather than performed, and the RNG is seeded.
"""

import random

import pytest

from resilience.retry import RetryPolicy


class Recorder:
    """Stands in for time.sleep and remembers what it was asked to wait."""

    def __init__(self):
        self.slept = []

    def __call__(self, seconds):
        self.slept.append(seconds)


def raise_connection_error():
    raise ConnectionError("x")


def test_returns_first_success_without_sleeping():
    sleeper = Recorder()
    p = RetryPolicy(sleep=sleeper)
    assert p.call(lambda: "ok") == "ok"
    assert sleeper.slept == []


def test_retries_then_succeeds():
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("nope")
        return "ok"

    p = RetryPolicy(max_attempts=3, sleep=Recorder(), rng=random.Random(0))
    assert p.call(flaky) == "ok"
    assert len(attempts) == 3


def test_gives_up_after_max_attempts_and_reraises_last():
    attempts = []

    def always_fail():
        attempts.append(1)
        raise ConnectionError(f"fail {len(attempts)}")

    p = RetryPolicy(max_attempts=4, sleep=Recorder(), rng=random.Random(0))
    with pytest.raises(ConnectionError, match="fail 4"):
        p.call(always_fail)
    assert len(attempts) == 4


def test_sleeps_between_attempts_not_after_the_last():
    sleeper = Recorder()
    p = RetryPolicy(max_attempts=3, sleep=sleeper, rng=random.Random(0))
    with pytest.raises(ConnectionError):
        p.call(raise_connection_error)
    assert len(sleeper.slept) == 2


def test_non_retryable_fails_fast():
    attempts = []

    def bad_request():
        attempts.append(1)
        raise ValueError("400")

    p = RetryPolicy(
        max_attempts=5,
        retryable=lambda e: isinstance(e, ConnectionError),
        sleep=Recorder(),
    )
    with pytest.raises(ValueError):
        p.call(bad_request)
    assert len(attempts) == 1


def test_delay_never_exceeds_max_delay_or_goes_negative():
    p = RetryPolicy(base_delay=0.5, max_delay=2.0, rng=random.Random(1234))
    for attempt in range(1, 12):
        for _ in range(50):
            delay = p.delay_for(attempt)
            assert 0.0 <= delay <= 2.0


def test_delay_grows_exponentially_in_expectation():
    p = RetryPolicy(base_delay=0.1, max_delay=100.0, rng=random.Random(7))

    def mean(attempt):
        return sum(p.delay_for(attempt) for _ in range(400)) / 400

    assert mean(1) < mean(3) < mean(5)


def test_on_attempt_callback_counts_attempts():
    seen = []
    p = RetryPolicy(max_attempts=3, sleep=Recorder(), rng=random.Random(0))
    p.on_attempt = seen.append
    with pytest.raises(ConnectionError):
        p.call(raise_connection_error)
    assert seen == [1, 2, 3]


def test_max_attempts_one_means_no_retry():
    attempts = []

    def counted():
        attempts.append(1)
        raise ConnectionError("x")

    p = RetryPolicy(max_attempts=1, sleep=Recorder())
    with pytest.raises(ConnectionError):
        p.call(counted)
    assert len(attempts) == 1


def test_zero_base_delay_still_retries_without_waiting():
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) < 2:
            raise ConnectionError("nope")
        return "ok"

    sleeper = Recorder()
    p = RetryPolicy(max_attempts=2, base_delay=0.0, sleep=sleeper)
    assert p.call(flaky) == "ok"
    assert sleeper.slept == [0.0]
