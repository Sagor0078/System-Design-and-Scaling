"""Prometheus instrumentation.

One dedicated registry rather than the global default, so a test importing this
module twice cannot trip duplicate-registration errors, and so ``/metrics``
exposes exactly what this service declares.

The label discipline matters more than it looks: route labels come from the
matched *route template* (``/orders/{order_id}``), never the raw path. A raw
path would mint a new time series per order id, and a vulnerability scanner
walking 10,000 URLs would permanently enlarge the Prometheus index.
"""

from __future__ import annotations

from typing import Any

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

from resilience.circuit_breaker import CircuitState

REGISTRY = CollectorRegistry()

#: Label used for any request that matched no route. Keeps cardinality bounded.
UNMATCHED_ROUTE = "unmatched"

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests served, by route template, method and status code.",
    ["route", "method", "status"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Wall-clock request duration in seconds.",
    ["route", "method"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

DEPENDENCY_CALLS = Counter(
    "dependency_calls_total",
    "Outbound dependency calls, by outcome "
    "(success, failure, circuit_open, degraded, no_fallback).",
    ["dependency", "outcome"],
    registry=REGISTRY,
)

RETRY_ATTEMPTS = Counter(
    "retry_attempts_total",
    "Attempts made against a dependency, including the first try.",
    ["dependency"],
    registry=REGISTRY,
)

DEGRADED_RESPONSES = Counter(
    "degraded_responses_total",
    "Responses served from stale cache because the dependency was unavailable.",
    ["route"],
    registry=REGISTRY,
)

BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state: 0 = closed, 1 = half-open, 2 = open.",
    ["dependency"],
    registry=REGISTRY,
)

#: The documented encoding. Grafana's state-timeline panel maps these back.
_STATE_VALUES = {
    CircuitState.CLOSED: 0.0,
    CircuitState.HALF_OPEN: 1.0,
    CircuitState.OPEN: 2.0,
}


def route_label(request: Any) -> str:
    """The matched route template, or ``unmatched``.

    Starlette puts the matched ``APIRoute`` in ``request.scope["route"]``. When
    nothing matched there is no template to report, and reporting the raw URL
    would be unbounded, so every unmatched request shares one label.
    """
    route = getattr(request, "scope", {}).get("route")
    path = getattr(route, "path", None)
    return path if path else UNMATCHED_ROUTE


def observe_request(route: str, method: str, status: int, duration: float) -> None:
    REQUESTS.labels(route=route, method=method, status=str(status)).inc()
    REQUEST_LATENCY.labels(route=route, method=method).observe(duration)


def set_breaker_state(name: str, state: CircuitState) -> None:
    BREAKER_STATE.labels(dependency=name).set(_STATE_VALUES[state])


def record_dependency_call(dependency: str, outcome: str) -> None:
    DEPENDENCY_CALLS.labels(dependency=dependency, outcome=outcome).inc()


def record_retry_attempt(dependency: str) -> None:
    RETRY_ATTEMPTS.labels(dependency=dependency).inc()


def record_degraded(route: str) -> None:
    DEGRADED_RESPONSES.labels(route=route).inc()


def render() -> tuple[bytes, str]:
    """Body and content type for the ``/metrics`` endpoint."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
