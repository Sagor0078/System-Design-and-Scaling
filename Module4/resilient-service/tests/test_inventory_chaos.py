"""Chaos-knob validation on the inventory dependency."""

import random

from inventory.main import ChaosState, stock_for


def test_defaults_are_healthy():
    s = ChaosState()
    assert s.fail_rate == 0.0
    assert s.latency_ms == 0
    assert s.down is False


def test_fail_rate_is_clamped_to_unit_interval():
    assert ChaosState(fail_rate=1.7).fail_rate == 1.0
    assert ChaosState(fail_rate=-0.2).fail_rate == 0.0


def test_negative_latency_is_rejected():
    assert ChaosState(latency_ms=-50).latency_ms == 0


def test_should_fail_is_exact_at_boundaries():
    # A 1.0 fail rate must never let a request through, and 0.0 must never
    # drop one, whatever the RNG happens to return.
    rng = random.Random(0)
    assert all(ChaosState(fail_rate=1.0).should_fail(rng) for _ in range(50))
    assert not any(ChaosState(fail_rate=0.0).should_fail(rng) for _ in range(50))


def test_should_fail_is_probabilistic_in_between():
    rng = random.Random(1234)
    s = ChaosState(fail_rate=0.5)
    hits = sum(s.should_fail(rng) for _ in range(1000))
    assert 400 < hits < 600


def test_reset_clears_injected_faults():
    s = ChaosState(fail_rate=1.0, latency_ms=3000, down=True)
    s.reset()
    assert (s.fail_rate, s.latency_ms, s.down) == (0.0, 0, False)


def test_apply_clamps_and_updates_in_place():
    s = ChaosState()
    s.apply(fail_rate=2.0, latency_ms=-1, down=True)
    assert (s.fail_rate, s.latency_ms, s.down) == (1.0, 0, True)


def test_apply_ignores_omitted_fields():
    s = ChaosState(fail_rate=0.3, latency_ms=100, down=False)
    s.apply(down=True)
    assert (s.fail_rate, s.latency_ms, s.down) == (0.3, 100, True)


def test_stock_is_deterministic_per_sku():
    assert stock_for("widget-1") == stock_for("widget-1")
    assert stock_for("widget-1") != stock_for("widget-2")


def test_stock_is_non_negative():
    assert all(stock_for(f"sku-{i}") >= 0 for i in range(200))
