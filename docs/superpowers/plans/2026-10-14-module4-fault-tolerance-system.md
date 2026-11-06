# Module 4 Resilient Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `Module4/fault-tolerance-system` — a FastAPI service that survives a failing dependency and exposes why, through metrics, traces, logs, alerts, a verifying chaos harness, and a Kubernetes overlay.

**Architecture:** A pure-Python `resilience/` package (circuit breaker, retry with jittered backoff, stale-cache degradation) with injected clock/sleep/RNG so it is testable without containers. An `orders` FastAPI service composes those as timeout → retry → breaker → fallback around an httpx call to an `inventory` service that can be told to fail. Prometheus scrapes both, Alertmanager receives rules, OpenTelemetry ships spans to Jaeger via a collector, Grafana is provisioned with a dashboard.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, httpx, prometheus-client, opentelemetry-sdk + instrumentation for FastAPI/httpx, Docker Compose, Prometheus, Alertmanager, Grafana, Jaeger, OTel Collector, pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-module4-reliability-observability-design.md`

## Global Constraints

- Python `>=3.12`; `.python-version` contains `3.12` (matches Modules 2 and 3).
- `resilience/` imports only the Python standard library — no FastAPI, no httpx, no prometheus_client. This is what makes it unit-testable and is the module's teaching point.
- Clock, sleep, and RNG are constructor-injected in `resilience/`; tests never call `time.sleep`.
- Telemetry failure must never break request handling.
- `/health/live` never checks dependencies. `/health/ready` may.
- A degraded order is HTTP 200 with `"degraded": true`, never a 5xx.
- Compose is the primary documented path; `k8s/` is an overlay.
- Pin dependency versions in `requirements.txt`, following Module 3's style.
- Do not modify Modules 1–3 or the root `README.md`.

## Review Focus

1. **Concurrent calls through one breaker** — two threads failing at the same instant must not double-count past the threshold or lose a state transition; the breaker needs a lock. (Task 2)
2. **`recovery_timeout` boundary** — at exactly `recovery_timeout` seconds the breaker must move to HALF_OPEN, not one tick later; and a zero timeout must not mean "never recover". (Task 2)
3. **`max_delay` cap under jitter** — full jitter must never produce a delay above `max_delay`, and never a negative delay. (Task 3)
4. **Cold cache under an open breaker** — degradation with nothing cached must raise a distinguishable error so the service returns 503 rather than a 200 claiming empty stock. (Task 4)
5. **Metrics label cardinality** — unknown paths (404 scans) must be recorded under the matched route template or a single `unmatched` label, never the raw URL, or Prometheus memory grows without bound. (Task 5)

---

### Task 1: Project scaffolding

**Files:**
- Create: `Module4/fault-tolerance-system/.python-version`
- Create: `Module4/fault-tolerance-system/pyproject.toml`
- Create: `Module4/fault-tolerance-system/requirements.txt`
- Create: `Module4/fault-tolerance-system/Dockerfile`
- Create: `Module4/fault-tolerance-system/.dockerignore`
- Create: `Module4/fault-tolerance-system/resilience/__init__.py`
- Create: `Module4/fault-tolerance-system/tests/__init__.py`
- Create: `Module4/fault-tolerance-system/conftest.py`

**Interfaces:**
- Consumes: nothing.
- Produces: an installable project root; `pytest` runnable from `Module4/fault-tolerance-system/`.

- [ ] **Step 1: Create the directory tree and version pin**

```bash
mkdir -p Module4/fault-tolerance-system/{resilience,orders,inventory,observability,chaos,tests}
mkdir -p Module4/fault-tolerance-system/{prometheus,alertmanager,otel,k8s}
mkdir -p Module4/fault-tolerance-system/grafana/provisioning/{datasources,dashboards}
mkdir -p Module4/fault-tolerance-system/grafana/dashboards
echo "3.12" > Module4/fault-tolerance-system/.python-version
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "fault-tolerance-system"
version = "0.1.0"
description = "Module 4 - reliability, observability and fault tolerance demo"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `requirements.txt` with pinned versions**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
prometheus-client==0.21.1
opentelemetry-sdk==1.29.0
opentelemetry-exporter-otlp-proto-grpc==1.29.0
opentelemetry-instrumentation-fastapi==0.50b0
opentelemetry-instrumentation-httpx==0.50b0
pytest==8.3.4
anyio==4.8.0
```

- [ ] **Step 4: Write the `Dockerfile` (one image, both services)**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "orders.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 5: Write `conftest.py`**

The async client tests use anyio's pytest plugin (anyio ships with FastAPI), which
requires an `anyio_backend` fixture, and the suite is run from the project root so
`resilience`, `orders` and friends import as top-level packages:

```python
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def anyio_backend():
    return "asyncio"
```

- [ ] **Step 6: Create empty package markers and verify pytest collects nothing**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest -q`
Expected: `no tests ran` (exit code 5), not an import error.

- [ ] **Step 7: Commit**

```bash
git add Module4/fault-tolerance-system
git commit -m "feat(module4): scaffold resilient-service project"
```

---

### Task 2: Circuit breaker

**Files:**
- Create: `Module4/fault-tolerance-system/resilience/circuit_breaker.py`
- Test: `Module4/fault-tolerance-system/tests/test_circuit_breaker.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class CircuitState(StrEnum)` with members `CLOSED`, `OPEN`, `HALF_OPEN`.
  - `class CircuitOpenError(RuntimeError)`.
  - `class CircuitBreaker(name: str, failure_threshold: int = 5, recovery_timeout: float = 10.0, half_open_max_calls: int = 1, success_threshold: int = 1, clock: Callable[[], float] = time.monotonic)`.
  - Methods: `call(fn, *args, **kwargs)` (raises `CircuitOpenError` when open), `state` property returning `CircuitState`, `on_state_change` callback attribute taking `(name, CircuitState)`.

- [ ] **Step 1: Write the failing tests**

```python
import threading
import pytest
from resilience.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


class FakeClock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, s): self.now += s


def boom(): raise ValueError("dependency failed")


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
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=1.0,
                        half_open_max_calls=1, clock=clock)
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
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=1.0,
                        half_open_max_calls=2, success_threshold=2, clock=clock)
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
        try: cb.call(boom)
        except Exception: pass
    threads = [threading.Thread(target=fail) for _ in range(40)]
    for t in threads: t.start()
    for t in threads: t.join(5)
    assert cb.state is CircuitState.CLOSED
    assert cb.failure_count == 40


def test_state_change_callback_fires():
    seen = []
    cb = CircuitBreaker("orders", failure_threshold=1, clock=FakeClock())
    cb.on_state_change = lambda name, state: seen.append((name, state))
    with pytest.raises(ValueError):
        cb.call(boom)
    assert seen == [("orders", CircuitState.OPEN)]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_circuit_breaker.py -q`
Expected: collection error — `ModuleNotFoundError: No module named 'resilience.circuit_breaker'`.

- [ ] **Step 3: Implement the breaker**

Use `threading.RLock` around every state read and mutation. Key points: `state` is a *computed* property (an OPEN breaker whose `recovery_timeout` has elapsed reports HALF_OPEN and consumes a probe slot on the next `call`); the elapsed check is `>=` so the boundary test passes; a half-open failure resets `opened_at` to now; `failure_count` is a public attribute for the concurrency test; `on_state_change` is invoked outside the lock.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_circuit_breaker.py -q`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add Module4/fault-tolerance-system/resilience/circuit_breaker.py Module4/fault-tolerance-system/tests/test_circuit_breaker.py
git commit -m "feat(module4): add circuit breaker with half-open probing"
```

---

### Task 3: Retry with jittered backoff

**Files:**
- Create: `Module4/fault-tolerance-system/resilience/retry.py`
- Test: `Module4/fault-tolerance-system/tests/test_retry.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class RetryPolicy(max_attempts: int = 3, base_delay: float = 0.1, max_delay: float = 2.0, retryable: Callable[[BaseException], bool] = lambda e: True, sleep: Callable[[float], None] = time.sleep, rng: random.Random | None = None)`.
  - `RetryPolicy.delay_for(attempt: int) -> float` — full jitter, `attempt` is 1-based.
  - `RetryPolicy.call(fn, *args, **kwargs)` — re-raises the last exception after exhausting attempts.
  - `RetryPolicy.on_attempt: Callable[[int], None] | None` — fired per attempt, for the metrics counter.

- [ ] **Step 1: Write the failing tests**

```python
import random
import pytest
from resilience.retry import RetryPolicy


class Recorder:
    def __init__(self): self.slept = []
    def __call__(self, s): self.slept.append(s)


def test_returns_first_success_without_sleeping():
    sleeper = Recorder()
    p = RetryPolicy(sleep=sleeper)
    assert p.call(lambda: "ok") == "ok"
    assert sleeper.slept == []


def test_retries_then_succeeds():
    attempts = []
    def flaky():
        attempts.append(1)
        if len(attempts) < 3: raise ConnectionError("nope")
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
        p.call(lambda: (_ for _ in ()).throw(ConnectionError("x")))
    assert len(sleeper.slept) == 2


def test_non_retryable_fails_fast():
    attempts = []
    def bad_request():
        attempts.append(1)
        raise ValueError("400")
    p = RetryPolicy(max_attempts=5, retryable=lambda e: isinstance(e, ConnectionError),
                    sleep=Recorder())
    with pytest.raises(ValueError):
        p.call(bad_request)
    assert len(attempts) == 1


def test_delay_never_exceeds_max_delay_or_goes_negative():
    p = RetryPolicy(base_delay=0.5, max_delay=2.0, rng=random.Random(1234))
    for attempt in range(1, 12):
        for _ in range(50):
            d = p.delay_for(attempt)
            assert 0.0 <= d <= 2.0


def test_delay_grows_exponentially_in_expectation():
    p = RetryPolicy(base_delay=0.1, max_delay=100.0, rng=random.Random(7))
    mean = lambda a: sum(p.delay_for(a) for _ in range(400)) / 400
    assert mean(1) < mean(3) < mean(5)


def test_on_attempt_callback_counts_attempts():
    seen = []
    p = RetryPolicy(max_attempts=3, sleep=Recorder(), rng=random.Random(0))
    p.on_attempt = seen.append
    with pytest.raises(ConnectionError):
        p.call(lambda: (_ for _ in ()).throw(ConnectionError("x")))
    assert seen == [1, 2, 3]


def test_max_attempts_one_means_no_retry():
    attempts = []
    p = RetryPolicy(max_attempts=1, sleep=Recorder())
    with pytest.raises(ConnectionError):
        p.call(lambda: (attempts.append(1), (_ for _ in ()).throw(ConnectionError("x")))[1])
    assert len(attempts) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_retry.py -q`
Expected: `ModuleNotFoundError: No module named 'resilience.retry'`.

- [ ] **Step 3: Implement `RetryPolicy`**

`delay_for(attempt)` computes `min(base_delay * 2 ** (attempt - 1), max_delay)` then returns `rng.uniform(0, cap)` — full jitter, bounded by `max_delay`, never negative. `call` loops `1..max_attempts`, fires `on_attempt`, returns on success, re-raises immediately when `retryable(exc)` is false or the attempt was the last, and otherwise sleeps `delay_for(attempt)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_retry.py -q`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add Module4/fault-tolerance-system/resilience/retry.py Module4/fault-tolerance-system/tests/test_retry.py
git commit -m "feat(module4): add retry policy with full-jitter backoff"
```

---

### Task 4: Graceful degradation cache

**Files:**
- Create: `Module4/fault-tolerance-system/resilience/degradation.py`
- Test: `Module4/fault-tolerance-system/tests/test_degradation.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class NoFallbackAvailable(RuntimeError)`.
  - `@dataclass(frozen=True) class Fallback: value: Any; stale: bool; age_seconds: float`.
  - `class StaleCache(ttl: float | None = None, clock: Callable[[], float] = time.monotonic)` with `put(key, value)`, `get_fresh(key) -> Fallback | None`, and `fallback(key) -> Fallback` (raises `NoFallbackAvailable` on a cold cache).

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from resilience.degradation import StaleCache, Fallback, NoFallbackAvailable


class FakeClock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, s): self.now += s


def test_cold_cache_raises_rather_than_returning_empty():
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


def test_keys_are_independent():
    c = StaleCache(clock=FakeClock())
    c.put("a", 1)
    with pytest.raises(NoFallbackAvailable):
        c.fallback("b")
    assert c.fallback("a").value == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_degradation.py -q`
Expected: `ModuleNotFoundError: No module named 'resilience.degradation'`.

- [ ] **Step 3: Implement `StaleCache`**

Dict of `key -> (value, stored_at)` under a `threading.Lock`. `get_fresh` returns `None` when missing or when `ttl is not None and age >= ttl`. `fallback` ignores the TTL entirely — that is the whole point — and raises `NoFallbackAvailable` only when the key was never stored.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_degradation.py -q`
Expected: 8 passed.

- [ ] **Step 5: Export the package surface in `resilience/__init__.py`**

```python
from resilience.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from resilience.degradation import Fallback, NoFallbackAvailable, StaleCache
from resilience.retry import RetryPolicy

__all__ = ["CircuitBreaker", "CircuitOpenError", "CircuitState", "Fallback",
           "NoFallbackAvailable", "StaleCache", "RetryPolicy"]
```

- [ ] **Step 6: Run the whole suite and commit**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest -q`
Expected: 29 passed.

```bash
git add Module4/fault-tolerance-system/resilience Module4/fault-tolerance-system/tests
git commit -m "feat(module4): add stale-cache graceful degradation"
```

---

### Task 5: Observability plumbing

**Files:**
- Create: `Module4/fault-tolerance-system/observability/__init__.py`
- Create: `Module4/fault-tolerance-system/observability/metrics.py`
- Create: `Module4/fault-tolerance-system/observability/logging.py`
- Create: `Module4/fault-tolerance-system/observability/otel.py`
- Test: `Module4/fault-tolerance-system/tests/test_metrics.py`

**Interfaces:**
- Consumes: `CircuitState` from Task 2.
- Produces:
  - `metrics.REGISTRY`, and collectors `REQUESTS`, `REQUEST_LATENCY`, `DEPENDENCY_CALLS`, `RETRY_ATTEMPTS`, `DEGRADED_RESPONSES`, `BREAKER_STATE`.
  - `metrics.route_label(request) -> str` — the matched route template, or `"unmatched"`.
  - `metrics.set_breaker_state(name: str, state: CircuitState) -> None`.
  - `metrics.render() -> tuple[bytes, str]` — body and content type for `/metrics`.
  - `logging.configure_logging(service: str) -> None` — JSON lines carrying `trace_id`/`span_id`.
  - `otel.setup_tracing(service_name: str, app=None) -> None` — never raises.

- [ ] **Step 1: Write the failing tests**

```python
from resilience.circuit_breaker import CircuitState
from observability import metrics


class FakeRoute:
    def __init__(self, path): self.path = path


class FakeRequest:
    def __init__(self, route=None, url_path="/raw"):
        self.scope = {"route": route} if route else {}
        self.url = type("U", (), {"path": url_path})()


def test_route_label_uses_template_not_raw_path():
    req = FakeRequest(route=FakeRoute("/orders/{order_id}"), url_path="/orders/8f21a")
    assert metrics.route_label(req) == "/orders/{order_id}"


def test_route_label_collapses_unmatched_paths():
    assert metrics.route_label(FakeRequest(url_path="/wp-admin.php")) == "unmatched"


def test_breaker_state_gauge_maps_states_to_numbers():
    metrics.set_breaker_state("inventory", CircuitState.CLOSED)
    assert metrics.BREAKER_STATE.labels(dependency="inventory")._value.get() == 0.0
    metrics.set_breaker_state("inventory", CircuitState.HALF_OPEN)
    assert metrics.BREAKER_STATE.labels(dependency="inventory")._value.get() == 1.0
    metrics.set_breaker_state("inventory", CircuitState.OPEN)
    assert metrics.BREAKER_STATE.labels(dependency="inventory")._value.get() == 2.0


def test_render_returns_prometheus_text_and_content_type():
    body, content_type = metrics.render()
    assert b"circuit_breaker_state" in body
    assert "text/plain" in content_type
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_metrics.py -q`
Expected: `ModuleNotFoundError: No module named 'observability'`.

- [ ] **Step 3: Implement the three observability modules**

`metrics.py`: a dedicated `CollectorRegistry`; `REQUESTS = Counter("http_requests_total", ..., ["route","method","status"])`; `REQUEST_LATENCY = Histogram("http_request_duration_seconds", ..., ["route","method"])` with buckets `(0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2.5,5,10)`; `DEPENDENCY_CALLS = Counter(..., ["dependency","outcome"])`; `RETRY_ATTEMPTS = Counter(..., ["dependency"])`; `DEGRADED_RESPONSES = Counter(..., ["route"])`; `BREAKER_STATE = Gauge("circuit_breaker_state", ..., ["dependency"])` with the documented mapping CLOSED=0, HALF_OPEN=1, OPEN=2. `route_label` reads `request.scope.get("route")` and returns its `path`, falling back to the literal `"unmatched"` — never the raw URL.

`logging.py`: a `logging.Formatter` emitting one JSON object per line (`ts`, `level`, `service`, `logger`, `msg`, and `trace_id`/`span_id` pulled from the current OTel span when one is recording), installed on the root logger.

`otel.py`: build a `TracerProvider` with a `Resource` naming the service, an `OTLPSpanExporter` pointed at `OTEL_EXPORTER_OTLP_ENDPOINT`, a `BatchSpanProcessor`, then instrument FastAPI and httpx. Wrap the whole body in `try/except Exception` and log a warning on failure, because telemetry must never break request handling.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_metrics.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add Module4/fault-tolerance-system/observability Module4/fault-tolerance-system/tests/test_metrics.py
git commit -m "feat(module4): add metrics, JSON logging and OTel tracing setup"
```

---

### Task 6: Inventory service with chaos controls

**Files:**
- Create: `Module4/fault-tolerance-system/inventory/__init__.py`
- Create: `Module4/fault-tolerance-system/inventory/main.py`
- Test: `Module4/fault-tolerance-system/tests/test_inventory_chaos.py`

**Interfaces:**
- Consumes: `observability.metrics`, `observability.logging`, `observability.otel`.
- Produces: `inventory.main:app`; `ChaosState` with fields `fail_rate: float`, `latency_ms: int`, `down: bool`; routes `GET /stock/{sku}`, `POST /chaos`, `GET /chaos`, `POST /chaos/reset`, `GET /health/live`, `GET /health/ready`, `GET /metrics`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from inventory.main import ChaosState


def test_defaults_are_healthy():
    s = ChaosState()
    assert s.fail_rate == 0.0 and s.latency_ms == 0 and s.down is False


def test_fail_rate_is_clamped_to_unit_interval():
    assert ChaosState(fail_rate=1.7).fail_rate == 1.0
    assert ChaosState(fail_rate=-0.2).fail_rate == 0.0


def test_negative_latency_is_rejected():
    assert ChaosState(latency_ms=-50).latency_ms == 0


def test_should_fail_is_deterministic_at_boundaries():
    import random
    rng = random.Random(0)
    assert ChaosState(fail_rate=1.0).should_fail(rng) is True
    assert ChaosState(fail_rate=0.0).should_fail(rng) is False


def test_reset_clears_injected_faults():
    s = ChaosState(fail_rate=1.0, latency_ms=3000, down=True)
    s.reset()
    assert (s.fail_rate, s.latency_ms, s.down) == (0.0, 0, False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_inventory_chaos.py -q`
Expected: `ModuleNotFoundError: No module named 'inventory.main'`.

- [ ] **Step 3: Implement the inventory service**

`ChaosState` clamps in `__post_init__` (`fail_rate` into `[0,1]`, `latency_ms` to `>= 0`) and exposes `should_fail(rng)` as `rng.random() < self.fail_rate` with the `0.0`/`1.0` boundaries special-cased so they are exact. `GET /stock/{sku}` returns 503 immediately when `down`, sleeps `latency_ms` via `asyncio.sleep`, rolls `should_fail` and returns 500 on a hit, otherwise returns a deterministic quantity derived from the SKU so repeated calls agree. Every path records `REQUESTS` and `REQUEST_LATENCY` through a middleware using `route_label`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_inventory_chaos.py -q`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add Module4/fault-tolerance-system/inventory Module4/fault-tolerance-system/tests/test_inventory_chaos.py
git commit -m "feat(module4): add inventory dependency with fault injection"
```

---

### Task 7: Orders service composing the resilience stack

**Files:**
- Create: `Module4/fault-tolerance-system/orders/__init__.py`
- Create: `Module4/fault-tolerance-system/orders/config.py`
- Create: `Module4/fault-tolerance-system/orders/clients.py`
- Create: `Module4/fault-tolerance-system/orders/main.py`
- Test: `Module4/fault-tolerance-system/tests/test_orders_client.py`
- Test: `Module4/fault-tolerance-system/tests/test_orders_api.py`

**Interfaces:**
- Consumes: everything from Tasks 2–5.
- Produces:
  - `config.Settings` (from env: `INVENTORY_URL`, `REQUEST_TIMEOUT`, `BREAKER_FAILURE_THRESHOLD`, `BREAKER_RECOVERY_TIMEOUT`, `RETRY_MAX_ATTEMPTS`, `RETRY_BASE_DELAY`, `CACHE_TTL`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `SERVICE_NAME`).
  - `clients.InventoryClient(settings, transport=None)` with `async get_stock(sku) -> Fallback`, attribute `breaker`, and `ready() -> bool`.
  - `clients.DependencyError(RuntimeError)` — retryable; `clients.BadRequest(RuntimeError)` — not.
  - `orders.main:app` with `POST /orders`, `GET /orders/{order_id}`, `GET /health/live`, `GET /health/ready`, `GET /metrics`.

- [ ] **Step 1: Write the failing tests**

```python
import httpx
import pytest
from fastapi.testclient import TestClient


def _client(handler, **overrides):
    from orders.clients import InventoryClient
    from orders.config import Settings
    settings = Settings(inventory_url="http://inv", request_timeout=0.5,
                        retry_base_delay=0.0, **overrides)
    return InventoryClient(settings, transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_returns_fresh_value_on_success():
    async def ok(request): return httpx.Response(200, json={"sku": "a", "qty": 5})
    c = _client(ok)
    fb = await c.get_stock("a")
    assert fb.value["qty"] == 5 and fb.stale is False


@pytest.mark.anyio
async def test_serves_stale_value_when_dependency_dies():
    calls = {"n": 0}
    async def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1: return httpx.Response(200, json={"sku": "a", "qty": 5})
        return httpx.Response(500)
    c = _client(flaky, breaker_failure_threshold=2, retry_max_attempts=1)
    await c.get_stock("a")
    fb = await c.get_stock("a")
    assert fb.value["qty"] == 5 and fb.stale is True


@pytest.mark.anyio
async def test_cold_cache_failure_propagates():
    from resilience import NoFallbackAvailable
    async def dead(request): return httpx.Response(503)
    c = _client(dead, retry_max_attempts=1)
    with pytest.raises(NoFallbackAvailable):
        await c.get_stock("never-seen")


@pytest.mark.anyio
async def test_breaker_opens_and_stops_calling_dependency():
    from resilience import CircuitState
    seen = {"n": 0}
    async def dead(request):
        seen["n"] += 1
        return httpx.Response(500)
    c = _client(dead, breaker_failure_threshold=1, retry_max_attempts=1)
    with pytest.raises(Exception):
        await c.get_stock("x")
    before = seen["n"]
    with pytest.raises(Exception):
        await c.get_stock("x")
    assert c.breaker.state is CircuitState.OPEN
    assert seen["n"] == before


@pytest.mark.anyio
async def test_client_error_is_not_retried():
    seen = {"n": 0}
    async def not_found(request):
        seen["n"] += 1
        return httpx.Response(404)
    c = _client(not_found, retry_max_attempts=5)
    with pytest.raises(Exception):
        await c.get_stock("ghost")
    assert seen["n"] == 1


def test_liveness_is_green_even_when_dependency_is_down(monkeypatch):
    from orders.main import app
    with TestClient(app) as tc:
        assert tc.get("/health/live").status_code == 200


def test_metrics_endpoint_exposes_breaker_gauge():
    from orders.main import app
    with TestClient(app) as tc:
        body = tc.get("/metrics").text
    assert "circuit_breaker_state" in body
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_orders_client.py tests/test_orders_api.py -q`
Expected: `ModuleNotFoundError: No module named 'orders.clients'`.

- [ ] **Step 3: Implement config, client and app**

`Settings` is a frozen dataclass with a `from_env()` classmethod. `InventoryClient.get_stock` composes, outermost first: the breaker, then the retry policy, then the timed httpx call. It maps 5xx and transport errors to `DependencyError` (retryable) and 4xx to `BadRequest` (not retryable), records `DEPENDENCY_CALLS` per outcome, feeds `RETRY_ATTEMPTS` from `RetryPolicy.on_attempt`, and pushes breaker transitions into `set_breaker_state` via `on_state_change`. On `CircuitOpenError` or an exhausted retry it calls `cache.fallback(sku)`, letting `NoFallbackAvailable` escape. `POST /orders` returns 200 with `"degraded": true` when the fallback is stale and 503 when `NoFallbackAvailable` is raised. `/health/ready` returns 503 exactly when the breaker is open and the cache holds nothing for the requested warm-up key.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest -q`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add Module4/fault-tolerance-system/orders Module4/fault-tolerance-system/tests
git commit -m "feat(module4): add orders service with resilient inventory client"
```

---

### Task 8: Compose stack and observability configuration

**Files:**
- Create: `Module4/fault-tolerance-system/docker-compose.yml`
- Create: `Module4/fault-tolerance-system/prometheus/prometheus.yml`
- Create: `Module4/fault-tolerance-system/prometheus/alert_rules.yml`
- Create: `Module4/fault-tolerance-system/alertmanager/alertmanager.yml`
- Create: `Module4/fault-tolerance-system/otel/collector-config.yaml`
- Create: `Module4/fault-tolerance-system/grafana/provisioning/datasources/prometheus.yml`
- Create: `Module4/fault-tolerance-system/grafana/provisioning/dashboards/dashboards.yml`
- Create: `Module4/fault-tolerance-system/grafana/dashboards/orders.json`

**Interfaces:**
- Consumes: the two service images from Tasks 6 and 7.
- Produces: service names `orders`, `inventory`, `prometheus`, `alertmanager`, `grafana`, `jaeger`, `otel-collector` on network `module4_network`, ports 8000/8001/9090/9093/3000/16686.

- [ ] **Step 1: Write `docker-compose.yml`**

Both Python services build from the shared `Dockerfile` with different `command` and `SERVICE_NAME`. `orders` depends on `inventory` with `condition: service_healthy`. Every service gets a `healthcheck` (the Python ones curl `/health/live`), following Module 3's style. Named volumes for Prometheus and Grafana data.

- [ ] **Step 2: Write the Prometheus scrape and rule files**

`prometheus.yml`: 5s scrape interval, jobs `orders` → `orders:8000` and `inventory` → `inventory:8001`, `rule_files: [alert_rules.yml]`, `alerting` pointed at `alertmanager:9093`.

`alert_rules.yml`, four rules with the thresholds fixed by the spec:

```yaml
groups:
  - name: reliability
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{job="orders",status=~"5.."}[2m]))
            / sum(rate(http_requests_total{job="orders"}[2m])) > 0.05
        for: 2m
        labels: {severity: critical}
        annotations:
          summary: "orders 5xx rate above 5% for 2m"
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state{dependency="inventory"} == 2
        for: 30s
        labels: {severity: warning}
        annotations:
          summary: "circuit breaker to inventory is OPEN"
      - alert: HighLatencyP95
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket{job="orders"}[5m])) by (le)) > 1
        for: 2m
        labels: {severity: warning}
        annotations:
          summary: "orders p95 latency above 1s for 2m"
      - alert: TargetDown
        expr: up == 0
        for: 1m
        labels: {severity: critical}
        annotations:
          summary: "{{ $labels.job }} target is down"
```

- [ ] **Step 3: Write the Alertmanager, collector and Grafana provisioning files**

Alertmanager: a `null` receiver with `group_by: [alertname, severity]` — the wiring is the lesson, not paging. Collector: OTLP gRPC receiver on 4317, batch processor, `otlp/jaeger` exporter to `jaeger:4317`. Grafana datasource: Prometheus at `http://prometheus:9090`, default. Dashboard provider pointing at `/var/lib/grafana/dashboards`.

- [ ] **Step 4: Write `grafana/dashboards/orders.json`**

Six panels: request rate by status, error rate percentage, latency p50/p95/p99 from the histogram, breaker state timeline, degraded responses rate, retry attempts rate. Hand-written JSON with `"schemaVersion": 39` and explicit `targets[].expr`.

- [ ] **Step 5: Validate every config file parses**

Run:
```bash
cd Module4/fault-tolerance-system && python3 - <<'EOF'
import json, sys
try:
    import yaml
except ImportError:
    yaml = None
json.load(open("grafana/dashboards/orders.json"))
if yaml:
    for f in ["docker-compose.yml","prometheus/prometheus.yml","prometheus/alert_rules.yml",
              "alertmanager/alertmanager.yml","otel/collector-config.yaml",
              "grafana/provisioning/datasources/prometheus.yml",
              "grafana/provisioning/dashboards/dashboards.yml"]:
        yaml.safe_load(open(f))
print("configs parse")
EOF
```
Expected: `configs parse`. If `docker compose` is installed, also run `docker compose config -q` and expect no output.

- [ ] **Step 6: Commit**

```bash
git add Module4/fault-tolerance-system
git commit -m "feat(module4): add compose stack, Prometheus rules, Grafana dashboard"
```

---

### Task 9: Chaos harness

**Files:**
- Create: `Module4/fault-tolerance-system/chaos/__init__.py`
- Create: `Module4/fault-tolerance-system/chaos/run_chaos.py`
- Test: `Module4/fault-tolerance-system/tests/test_chaos_harness.py`

**Interfaces:**
- Consumes: the running Compose stack at runtime; nothing at import time.
- Produces: `parse_metrics(text) -> dict[str, float]`, `counter_delta(before, after, name, labels) -> float`, `verdict(assertions: list[tuple[str, bool]]) -> bool`, `Experiment` dataclass, `EXPERIMENTS: list[Experiment]`, and a `main()` CLI accepting `--experiment NAME`, `--orders-url`, `--inventory-url`, `--duration`.

- [ ] **Step 1: Write the failing tests for the parsing and verdict logic**

```python
from chaos.run_chaos import counter_delta, parse_metrics, verdict

SAMPLE = """
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{route="/orders",method="POST",status="200"} 12.0
http_requests_total{route="/orders",method="POST",status="503"} 3.0
circuit_breaker_state{dependency="inventory"} 2.0
degraded_responses_total{route="/orders"} 7.0
"""


def test_parse_metrics_reads_labelled_series():
    m = parse_metrics(SAMPLE)
    assert m['http_requests_total{method="POST",route="/orders",status="200"}'] == 12.0
    assert m['circuit_breaker_state{dependency="inventory"}'] == 2.0


def test_parse_metrics_ignores_comments():
    assert not any(k.startswith("#") for k in parse_metrics(SAMPLE))


def test_counter_delta_treats_missing_before_as_zero():
    after = parse_metrics(SAMPLE)
    assert counter_delta({}, after, "degraded_responses_total", {"route": "/orders"}) == 7.0


def test_counter_delta_subtracts_baseline():
    after = parse_metrics(SAMPLE)
    before = {'degraded_responses_total{route="/orders"}': 5.0}
    assert counter_delta(before, after, "degraded_responses_total", {"route": "/orders"}) == 2.0


def test_verdict_passes_when_all_assertions_hold():
    assert verdict([("breaker opened", True), ("degraded served", True)]) is True


def test_verdict_fails_when_any_assertion_breaks():
    assert verdict([("breaker opened", True), ("no 5xx", False)]) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_chaos_harness.py -q`
Expected: `ModuleNotFoundError: No module named 'chaos.run_chaos'`.

- [ ] **Step 3: Implement the harness**

`parse_metrics` normalises label order so keys are stable. The four experiments from the spec — `total_failure`, `latency`, `hard_kill`, `recovery` — each snapshot `/metrics`, drive load with `httpx`, set chaos through the inventory `/chaos` endpoint (or `docker kill`/`docker start` for `hard_kill`), snapshot again, and assert deltas: breaker reaches OPEN, `degraded_responses_total` rises, `orders` 5xx stays at zero while the cache is warm, and after recovery the gauge returns to 0. `main()` prints a pass/fail table and exits non-zero if any experiment fails.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest tests/test_chaos_harness.py -q`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add Module4/fault-tolerance-system/chaos Module4/fault-tolerance-system/tests/test_chaos_harness.py
git commit -m "feat(module4): add verifying chaos experiment harness"
```

---

### Task 10: Kubernetes overlay

**Files:**
- Create: `Module4/fault-tolerance-system/k8s/namespace.yaml`
- Create: `Module4/fault-tolerance-system/k8s/configmap.yaml`
- Create: `Module4/fault-tolerance-system/k8s/inventory.yaml`
- Create: `Module4/fault-tolerance-system/k8s/orders.yaml`
- Create: `Module4/fault-tolerance-system/k8s/hpa.yaml`
- Create: `Module4/fault-tolerance-system/k8s/kustomization.yaml`

**Interfaces:**
- Consumes: the image built in Task 1, tagged `module4/fault-tolerance-system:local`.
- Produces: namespace `module4`, Deployments `orders` and `inventory`, Services of the same names, and an HPA targeting `orders`.

- [ ] **Step 1: Write the manifests**

`orders.yaml`: 2 replicas; `livenessProbe` → `/health/live` (`initialDelaySeconds: 5`, `periodSeconds: 10`, `failureThreshold: 3`); `readinessProbe` → `/health/ready` (`periodSeconds: 5`, `failureThreshold: 2`); `startupProbe` → `/health/live` with `failureThreshold: 30`; `resources.requests` `100m`/`128Mi` and `limits` `500m`/`256Mi` (requests are required for the HPA to compute utilisation); pod annotations `prometheus.io/scrape: "true"`, `prometheus.io/port: "8000"`, `prometheus.io/path: "/metrics"`; env from the ConfigMap.

- [ ] **Step 2: Write `hpa.yaml`**

`autoscaling/v2`, `minReplicas: 2`, `maxReplicas: 6`, CPU `Utilization` target `60`, plus `behavior.scaleDown.stabilizationWindowSeconds: 120` so the demo does not flap.

- [ ] **Step 3: Validate the YAML parses and the probe endpoints differ**

Run:
```bash
cd Module4/fault-tolerance-system && python3 - <<'EOF'
import glob, yaml
for f in sorted(glob.glob("k8s/*.yaml")):
    list(yaml.safe_load_all(open(f)))
docs = list(yaml.safe_load_all(open("k8s/orders.yaml")))
dep = next(d for d in docs if d["kind"] == "Deployment")
c = dep["spec"]["template"]["spec"]["containers"][0]
assert c["livenessProbe"]["httpGet"]["path"] == "/health/live"
assert c["readinessProbe"]["httpGet"]["path"] == "/health/ready"
print("k8s manifests valid; probes point at distinct endpoints")
EOF
```
Expected: the success line. If `kubectl` is available, also `kubectl apply --dry-run=client -k k8s/`.

- [ ] **Step 4: Commit**

```bash
git add Module4/fault-tolerance-system/k8s
git commit -m "feat(module4): add Kubernetes overlay with probes and HPA"
```

---

### Task 11: README and final verification

**Files:**
- Create: `Module4/fault-tolerance-system/README.md`

**Interfaces:**
- Consumes: everything.
- Produces: the documented entry point.

- [ ] **Step 1: Write the README in Module 3's style**

Sections: title, one-paragraph summary, ASCII architecture diagram (copied from the spec), prerequisites table, numbered quick start (`docker compose up -d`, wait for health, generate traffic, open Grafana/Jaeger/Prometheus), the four chaos experiments as a runbook table with expected observations, endpoint reference table, project structure tree, "how it works" walking the timeout → retry → breaker → fallback chain, a probe-semantics note explaining why liveness ignores dependencies, the Kubernetes section, a `pytest` section, and a teardown command.

- [ ] **Step 2: Run the full suite**

Run: `cd Module4/fault-tolerance-system && python3 -m pytest -q`
Expected: every test passes.

- [ ] **Step 3: Byte-compile everything**

Run: `cd Module4/fault-tolerance-system && python3 -m compileall -q resilience orders inventory observability chaos`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add Module4/fault-tolerance-system/README.md
git commit -m "docs(module4): add resilient-service README and runbook"
```
