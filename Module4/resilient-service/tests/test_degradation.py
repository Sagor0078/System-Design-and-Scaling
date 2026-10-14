"""Stale-cache degradation behaviour."""

import pytest

from resilience.degradation import Fallback, NoFallbackAvailable, StaleCache


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_cold_cache_raises_rather_than_returning_empty():
    # The important case: never answer "qty 0" when the truth is "unknown".
    with pytest.raises(NoFallbackAvailable):
        StaleCache(clock=FakeClock()).fallback("sku-1")


def test_fallback_returns_last_known_value_marked_stale():
    c = StaleCache(clock=FakeClock())
    c.put("sku-1", {"qty": 7})
    fb = c.fallback("sku-1")
    assert isinstance(fb, Fallback)
    assert fb.value == {"qty": 7}
    assert fb.stale is True


def test_fallback_reports_age():
    clock = FakeClock()
    c = StaleCache(clock=clock)
    c.put("sku-1", {"qty": 7})
    clock.advance(42.0)
    assert c.fallback("sku-1").age_seconds == pytest.approx(42.0)


def test_put_overwrites_and_resets_age():
    clock = FakeClock()
    c = StaleCache(clock=clock)
    c.put("sku-1", {"qty": 1})
    clock.advance(10.0)
    c.put("sku-1", {"qty": 2})
    fb = c.fallback("sku-1")
    assert fb.value == {"qty": 2}
    assert fb.age_seconds == 0.0


def test_get_fresh_returns_none_on_miss():
    assert StaleCache(clock=FakeClock()).get_fresh("absent") is None


def test_get_fresh_returns_fresh_entry_not_marked_stale():
    c = StaleCache(ttl=30.0, clock=FakeClock())
    c.put("sku-1", {"qty": 3})
    fb = c.get_fresh("sku-1")
    assert fb.stale is False


def test_get_fresh_expires_past_ttl_but_fallback_still_serves():
    clock = FakeClock()
    c = StaleCache(ttl=30.0, clock=clock)
    c.put("sku-1", {"qty": 3})
    clock.advance(30.0)
    assert c.get_fresh("sku-1") is None
    assert c.fallback("sku-1").value == {"qty": 3}


def test_no_ttl_means_get_fresh_never_expires():
    clock = FakeClock()
    c = StaleCache(clock=clock)
    c.put("sku-1", {"qty": 3})
    clock.advance(10_000.0)
    assert c.get_fresh("sku-1").stale is False


def test_keys_are_independent():
    c = StaleCache(clock=FakeClock())
    c.put("a", 1)
    with pytest.raises(NoFallbackAvailable):
        c.fallback("b")
    assert c.fallback("a").value == 1


def test_fallback_error_names_the_key():
    with pytest.raises(NoFallbackAvailable, match="sku-9"):
        StaleCache(clock=FakeClock()).fallback("sku-9")
