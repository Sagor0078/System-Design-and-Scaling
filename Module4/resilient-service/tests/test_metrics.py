"""Metrics registry behaviour, especially label hygiene."""

from observability import metrics
from resilience.circuit_breaker import CircuitState


class FakeRoute:
    def __init__(self, path):
        self.path = path


class FakeRequest:
    def __init__(self, route=None, url_path="/raw"):
        self.scope = {"route": route} if route else {}
        self.url = type("U", (), {"path": url_path})()


def test_route_label_uses_template_not_raw_path():
    req = FakeRequest(route=FakeRoute("/orders/{order_id}"), url_path="/orders/8f21a")
    assert metrics.route_label(req) == "/orders/{order_id}"


def test_route_label_collapses_unmatched_paths():
    # Unbounded label cardinality is how a /metrics endpoint eats a Prometheus
    # server: a scanner hitting 10k random URLs must produce one series, not 10k.
    assert metrics.route_label(FakeRequest(url_path="/wp-admin.php")) == "unmatched"


def test_route_label_is_stable_across_distinct_unmatched_paths():
    labels = {
        metrics.route_label(FakeRequest(url_path=f"/junk-{i}")) for i in range(100)
    }
    assert labels == {"unmatched"}


def test_breaker_state_gauge_maps_states_to_numbers():
    metrics.set_breaker_state("inventory", CircuitState.CLOSED)
    assert metrics.BREAKER_STATE.labels(dependency="inventory")._value.get() == 0.0
    metrics.set_breaker_state("inventory", CircuitState.HALF_OPEN)
    assert metrics.BREAKER_STATE.labels(dependency="inventory")._value.get() == 1.0
    metrics.set_breaker_state("inventory", CircuitState.OPEN)
    assert metrics.BREAKER_STATE.labels(dependency="inventory")._value.get() == 2.0


def test_render_returns_prometheus_text_and_content_type():
    metrics.set_breaker_state("inventory", CircuitState.CLOSED)
    body, content_type = metrics.render()
    assert b"circuit_breaker_state" in body
    assert "text/plain" in content_type


def test_observe_request_records_counter_and_histogram():
    before = metrics.REQUESTS.labels(route="/t", method="GET", status="200")._value.get()
    metrics.observe_request(route="/t", method="GET", status=200, duration=0.01)
    after = metrics.REQUESTS.labels(route="/t", method="GET", status="200")._value.get()
    assert after - before == 1.0
    body, _ = metrics.render()
    assert b"http_request_duration_seconds" in body
