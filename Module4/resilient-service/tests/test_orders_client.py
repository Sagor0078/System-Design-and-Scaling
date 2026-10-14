"""The inventory client: timeout -> retry -> breaker -> fallback."""

import httpx
import pytest

from orders.clients import BadRequest, DependencyError, InventoryClient
from orders.config import Settings
from resilience import CircuitState, NoFallbackAvailable


def make_client(handler, **overrides):
    settings = Settings(
        inventory_url="http://inv",
        request_timeout=0.5,
        retry_base_delay=0.0,
        retry_max_delay=0.0,
        **overrides,
    )
    return InventoryClient(settings, transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_returns_fresh_value_on_success():
    def ok(request):
        return httpx.Response(200, json={"sku": "a", "qty": 5})

    fb = await make_client(ok).get_stock("a")
    assert fb.value["qty"] == 5
    assert fb.stale is False


@pytest.mark.anyio
async def test_serves_stale_value_when_dependency_dies():
    calls = {"n": 0}

    def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"sku": "a", "qty": 5})
        return httpx.Response(500)

    c = make_client(flaky, breaker_failure_threshold=2, retry_max_attempts=1)
    await c.get_stock("a")
    fb = await c.get_stock("a")
    assert fb.value["qty"] == 5
    assert fb.stale is True


@pytest.mark.anyio
async def test_cold_cache_failure_propagates():
    def dead(request):
        return httpx.Response(503)

    c = make_client(dead, retry_max_attempts=1)
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("never-seen")


@pytest.mark.anyio
async def test_breaker_opens_and_stops_calling_dependency():
    seen = {"n": 0}

    def dead(request):
        seen["n"] += 1
        return httpx.Response(500)

    c = make_client(dead, breaker_failure_threshold=1, retry_max_attempts=1)
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("x")
    before = seen["n"]
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("x")
    assert c.breaker.state is CircuitState.OPEN
    assert seen["n"] == before, "an open breaker must not touch the dependency"


@pytest.mark.anyio
async def test_client_error_is_not_retried():
    seen = {"n": 0}

    def not_found(request):
        seen["n"] += 1
        return httpx.Response(404)

    c = make_client(not_found, retry_max_attempts=5)
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("ghost")
    assert seen["n"] == 1, "a 4xx is our bug, not a transient fault"


@pytest.mark.anyio
async def test_server_error_is_retried_up_to_max_attempts():
    seen = {"n": 0}

    def dead(request):
        seen["n"] += 1
        return httpx.Response(500)

    c = make_client(dead, retry_max_attempts=3, breaker_failure_threshold=99)
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("x")
    assert seen["n"] == 3


@pytest.mark.anyio
async def test_timeout_is_treated_as_a_retryable_dependency_error():
    seen = {"n": 0}

    def slow(request):
        seen["n"] += 1
        raise httpx.ReadTimeout("too slow", request=request)

    c = make_client(slow, retry_max_attempts=2, breaker_failure_threshold=99)
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("x")
    assert seen["n"] == 2


@pytest.mark.anyio
async def test_recovery_closes_the_breaker_and_serves_fresh_again():
    state = {"fail": True}

    def toggling(request):
        if state["fail"]:
            return httpx.Response(500)
        return httpx.Response(200, json={"sku": "a", "qty": 9})

    c = make_client(
        toggling,
        breaker_failure_threshold=1,
        breaker_recovery_timeout=0.0,
        breaker_success_threshold=1,
        retry_max_attempts=1,
    )
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("a")
    state["fail"] = False
    fb = await c.get_stock("a")
    assert fb.value["qty"] == 9
    assert fb.stale is False
    assert c.breaker.state is CircuitState.CLOSED


@pytest.mark.anyio
async def test_recovery_needs_success_threshold_probes():
    # With the production default of two required successes, one good probe is
    # not enough to close the circuit -- a dependency that flaps should not be
    # declared healthy on the strength of a single call.
    state = {"fail": True}

    def toggling(request):
        if state["fail"]:
            return httpx.Response(500)
        return httpx.Response(200, json={"sku": "a", "qty": 9})

    c = make_client(
        toggling,
        breaker_failure_threshold=1,
        breaker_recovery_timeout=0.0,
        breaker_success_threshold=2,
        breaker_half_open_max_calls=2,
        retry_max_attempts=1,
    )
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("a")
    state["fail"] = False
    await c.get_stock("a")
    assert c.breaker.state is CircuitState.HALF_OPEN
    await c.get_stock("a")
    assert c.breaker.state is CircuitState.CLOSED


@pytest.mark.anyio
async def test_exception_types_are_distinguishable():
    def not_found(request):
        return httpx.Response(404)

    c = make_client(not_found, retry_max_attempts=1)
    with pytest.raises(BadRequest):
        await c.fetch_once("ghost")

    def dead(request):
        return httpx.Response(500)

    c2 = make_client(dead, retry_max_attempts=1)
    with pytest.raises(DependencyError):
        await c2.fetch_once("x")


@pytest.mark.anyio
async def test_ready_is_false_only_when_open_and_cache_cold():
    def dead(request):
        return httpx.Response(500)

    c = make_client(dead, breaker_failure_threshold=1, retry_max_attempts=1)
    assert c.ready() is True
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("x")
    assert c.breaker.state is CircuitState.OPEN
    assert c.ready() is False
