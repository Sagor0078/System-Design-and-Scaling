"""The orders HTTP surface, including probe semantics."""

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_factory(monkeypatch):
    """Build an orders app whose inventory transport we control."""

    def build(handler, **overrides):
        import orders.main as main
        from orders.clients import InventoryClient
        from orders.config import Settings

        settings = Settings(
            inventory_url="http://inv",
            request_timeout=0.5,
            retry_base_delay=0.0,
            retry_max_delay=0.0,
            **overrides,
        )
        main.app.state.inventory = InventoryClient(
            settings, transport=httpx.MockTransport(handler)
        )
        main.ORDERS.clear()
        return TestClient(main.app)

    return build


def ok(request):
    return httpx.Response(200, json={"sku": "widget", "qty": 42})


def dead(request):
    return httpx.Response(500)


def test_create_order_succeeds_with_live_inventory(client_factory):
    with client_factory(ok) as tc:
        r = tc.post("/orders", json={"sku": "widget", "quantity": 2})
    assert r.status_code == 201
    body = r.json()
    assert body["degraded"] is False
    assert body["available_qty"] == 42


def test_order_is_retrievable(client_factory):
    with client_factory(ok) as tc:
        created = tc.post("/orders", json={"sku": "widget", "quantity": 1}).json()
        fetched = tc.get(f"/orders/{created['order_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["order_id"] == created["order_id"]


def test_unknown_order_is_404(client_factory):
    with client_factory(ok) as tc:
        assert tc.get("/orders/nope").status_code == 404


def test_degrades_to_200_with_flag_when_inventory_dies(client_factory):
    calls = {"n": 0}

    def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"sku": "widget", "qty": 42})
        return httpx.Response(500)

    with client_factory(flaky, breaker_failure_threshold=1, retry_max_attempts=1) as tc:
        tc.post("/orders", json={"sku": "widget", "quantity": 1})
        r = tc.post("/orders", json={"sku": "widget", "quantity": 1})
    assert r.status_code == 200, "a warm cache must not produce a 5xx"
    assert r.json()["degraded"] is True
    assert r.json()["stale_age_seconds"] >= 0


def test_returns_503_when_inventory_dies_with_a_cold_cache(client_factory):
    with client_factory(dead, breaker_failure_threshold=1, retry_max_attempts=1) as tc:
        r = tc.post("/orders", json={"sku": "unknown-sku", "quantity": 1})
    assert r.status_code == 503
    assert "unavailable" in r.json()["detail"].lower()


def test_liveness_is_green_even_when_dependency_is_down(client_factory):
    with client_factory(dead, breaker_failure_threshold=1, retry_max_attempts=1) as tc:
        tc.post("/orders", json={"sku": "x", "quantity": 1})
        r = tc.get("/health/live")
    assert r.status_code == 200, (
        "liveness must ignore dependencies, or a dependency outage becomes a "
        "restart loop across every replica"
    )


def test_readiness_goes_red_when_breaker_open_and_cache_cold(client_factory):
    with client_factory(dead, breaker_failure_threshold=1, retry_max_attempts=1) as tc:
        assert tc.get("/health/ready").status_code == 200
        tc.post("/orders", json={"sku": "x", "quantity": 1})
        r = tc.get("/health/ready")
    assert r.status_code == 503


def test_readiness_stays_green_when_degradation_is_possible(client_factory):
    calls = {"n": 0}

    def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"sku": "widget", "qty": 42})
        return httpx.Response(500)

    with client_factory(flaky, breaker_failure_threshold=1, retry_max_attempts=1) as tc:
        tc.post("/orders", json={"sku": "widget", "quantity": 1})
        tc.post("/orders", json={"sku": "widget", "quantity": 1})
        r = tc.get("/health/ready")
    assert r.status_code == 200, "we can still serve, so stay in rotation"


def test_metrics_endpoint_exposes_breaker_gauge(client_factory):
    with client_factory(ok) as tc:
        body = tc.get("/metrics").text
    assert "circuit_breaker_state" in body
    assert "http_requests_total" in body


def test_degraded_responses_counter_increments(client_factory):
    from observability import metrics

    before = metrics.DEGRADED_RESPONSES.labels(route="/orders")._value.get()
    calls = {"n": 0}

    def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"sku": "widget", "qty": 42})
        return httpx.Response(500)

    with client_factory(flaky, breaker_failure_threshold=1, retry_max_attempts=1) as tc:
        tc.post("/orders", json={"sku": "widget", "quantity": 1})
        tc.post("/orders", json={"sku": "widget", "quantity": 1})
    after = metrics.DEGRADED_RESPONSES.labels(route="/orders")._value.get()
    assert after - before == 1.0


def test_unmatched_path_uses_a_single_metric_label(client_factory):
    from observability import metrics

    with client_factory(ok) as tc:
        for i in range(5):
            tc.get(f"/not-a-route-{i}")
    series = metrics.REQUESTS.labels(
        route="unmatched", method="GET", status="404"
    )._value.get()
    assert series >= 5
