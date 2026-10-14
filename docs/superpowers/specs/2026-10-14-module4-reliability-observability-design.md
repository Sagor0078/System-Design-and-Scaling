# Module 4 — Reliability, Observability & Fault Tolerance

**Date:** 2026-10-14
**Status:** Approved design, pending implementation plan
**Location:** `Module4/resilient-service/`

## Intent

Module 4 of the learning plan covers "make systems resilient and debuggable."
This module adds a self-contained demo where a service survives a failing
dependency, and where the operator can *see why* through metrics, traces, and
logs. It follows the pattern set by Modules 1–3: a Docker Compose stack with a
Python app, runnable locally on one machine, with a Kubernetes overlay for the
"deploy it for real" step.

Success criteria:

1. `docker compose up -d` yields a working service, a provisioned Grafana
   dashboard, and traces in Jaeger.
2. One command injects a dependency failure.
3. The dashboard, traces, and alerts visibly show the circuit breaker opening
   and the service degrading rather than failing.
4. `pytest` proves the breaker, retry, and degradation logic with no containers
   running and no real sleeps.

Non-goals (explicitly out of scope): a Makefile, `run_demo.sh`, a `Module4/README.md`
index page, root-README index edits, load testing (covered in Module 1), and any change to Modules 1–3.

## Architecture

```
                      ┌──────────────────┐
   client ──▶ orders-service :8000 ──timeout+retry+breaker──▶ inventory-service :8001
                      │   │                                    (/chaos: fail_rate,
                      │   │                                     latency_ms, down)
         /metrics ◀───┘   └──OTLP──▶ otel-collector ──▶ jaeger :16686
              ▲
              │ scrape
        prometheus :9090 ──▶ alertmanager :9093
              │
              └──▶ grafana :3000  (provisioned datasource + dashboard)
```

Seven containers. `orders-service` is the system under test; `inventory-service`
is the dependency that gets broken; the rest is the observability plane.

## Components

### `resilience/` — pure Python, no framework imports

The one reusable unit. Clock, sleep, and RNG are injected through the
constructor so behaviour is deterministic under test.

- `circuit_breaker.py` — states `CLOSED` / `OPEN` / `HALF_OPEN`. Config:
  `failure_threshold`, `recovery_timeout`, `half_open_max_calls`,
  `success_threshold`. Raises `CircuitOpenError` without calling through when
  open. Exposes `state` for the metrics gauge.
- `retry.py` — exponential backoff with full jitter. Config: `max_attempts`,
  `base_delay`, `max_delay`, and a `retryable` predicate so non-retryable
  errors fail fast.
- `degradation.py` — stale-value cache. On dependency failure, returns the last
  known value flagged as stale; raises only when nothing is cached.

Contract: callers compose these as timeout → retry → breaker → fallback. Nothing
in this package knows about HTTP, FastAPI, or Prometheus.

### `orders/` — the service under test

- `main.py` — FastAPI app. `POST /orders` (creates an order, consults
  inventory), `GET /orders/{id}`, `GET /health/live`, `GET /health/ready`,
  `GET /metrics`.
- `clients.py` — the inventory client, wrapping the httpx call in the
  resilience stack above. A degraded order returns HTTP 200 with
  `"degraded": true`, not a 500.
- `config.py` — environment-driven settings (dependency URL, timeout, breaker
  and retry tuning, OTLP endpoint).

Probe semantics, stated explicitly because getting this wrong is the common
bug: `/health/live` reports only whether the process is healthy and **never**
checks dependencies, so a dependency outage cannot cause a restart loop.
`/health/ready` returns 503 only when the breaker is open *and* no fallback
data exists, so the pod is pulled from rotation when it genuinely cannot serve.

### `inventory/` — the unreliable dependency

`GET /stock/{sku}` plus `POST /chaos` with `fail_rate` (0.0–1.0),
`latency_ms`, and `down` (hard 503). `GET /chaos` reports current state.
`POST /chaos/reset` clears it.

### `observability/`

- `otel.py` — OTel SDK setup, auto-instrumenting FastAPI and httpx, exporting
  OTLP to the collector. Retries and breaker rejections appear as spans.
- `metrics.py` — `prometheus_client` registry: `http_requests_total{route,
  method,status}`, `http_request_duration_seconds` histogram,
  `circuit_breaker_state` gauge, `dependency_calls_total{outcome}`,
  `retry_attempts_total`, `degraded_responses_total`.
- `logging.py` — JSON log formatter injecting `trace_id` and `span_id`, so
  logs and Jaeger cross-reference.

### Configuration files

- `prometheus/prometheus.yml` — scrapes both services.
- `prometheus/alert_rules.yml` — high 5xx rate (>5% over 2m), circuit breaker
  open, p95 latency above 1s for 2m, target down.
- `alertmanager/alertmanager.yml` — a null receiver with grouping configured;
  the point is to show the wiring, not to send real pages.
- `otel/collector-config.yaml` — OTLP receiver → batch processor → Jaeger
  exporter.
- `grafana/provisioning/` — datasource and dashboard providers.
- `grafana/dashboards/orders.json` — request rate, error rate, p50/p95/p99
  latency, breaker state timeline, degraded-response rate.

### `chaos/`

`run_chaos.py` runs four named experiments, each scraping `/metrics` before and
after and printing a pass/fail table, so the module's claims are verifiable
without eyeballing Grafana:

1. **Total dependency failure** — `fail_rate=1.0`; expect the breaker to open
   and degraded responses to rise, with no 5xx from `orders`.
2. **Latency injection** — `latency_ms` above the client timeout; expect
   timeouts, retries, then the breaker opening.
3. **Hard kill** — `docker kill` on the dependency; expect readiness to flip
   and liveness to stay green.
4. **Recovery** — restore the dependency; expect `HALF_OPEN` then `CLOSED`,
   and degraded responses to stop.

### `k8s/`

Deployment (both probes pointed at the two distinct endpoints, resource
requests and limits), Service, ConfigMap, HPA on CPU (min 2, max 6), and pod
scrape annotations. The README notes kube-prometheus-stack as the metrics path
on a cluster. Compose remains the primary documented route.

### `tests/`

Pytest over `resilience/` only, written before the implementation:

- threshold failures trip the breaker to `OPEN`
- `OPEN` rejects without invoking the wrapped callable
- `HALF_OPEN` success closes; `HALF_OPEN` failure reopens
- `recovery_timeout` elapsing moves `OPEN` → `HALF_OPEN`
- backoff delays stay within jitter bounds and respect `max_delay`
- non-retryable exceptions are not retried
- retries give up after `max_attempts` and propagate the last error
- degradation returns cached data flagged stale; raises when the cache is empty

All deterministic: injected clock, injected sleep, seeded RNG.

## Data flow

A `POST /orders` request: FastAPI middleware starts a span and increments the
request counter → `clients.py` calls inventory under a timeout → on failure,
retry with jittered backoff (each attempt a child span, `retry_attempts_total`
incremented) → repeated failures trip the breaker (`circuit_breaker_state`
gauge updated) → subsequent calls short-circuit immediately and fall back to
the stale cache, returning 200 with `"degraded": true` and incrementing
`degraded_responses_total`. Prometheus scrapes this; the alert rules fire;
Grafana shows it; Jaeger holds the span tree; the JSON logs carry the trace ID.

## Error handling

| Condition | Behaviour |
|---|---|
| Dependency slow | httpx timeout → retry → breaker |
| Dependency 5xx | retryable → retry → breaker |
| Dependency 4xx | non-retryable → fail fast, no retry |
| Breaker open, cache warm | 200 with `degraded: true` |
| Breaker open, cache cold | 503, `/health/ready` reports not-ready |
| Collector unreachable | OTel export fails silently; the service keeps serving |

Telemetry failure never breaks request handling.

## Files

```
Module4/
└── resilient-service/
    ├── README.md                  (quick start, architecture, chaos runbook)
    ├── docker-compose.yml
    ├── pyproject.toml
    ├── requirements.txt
    ├── .python-version            (3.12)
    ├── Dockerfile
    ├── resilience/{__init__,circuit_breaker,retry,degradation}.py
    ├── orders/{__init__,main,clients,config}.py
    ├── inventory/{__init__,main}.py
    ├── observability/{__init__,otel,metrics,logging}.py
    ├── chaos/run_chaos.py
    ├── prometheus/{prometheus.yml,alert_rules.yml}
    ├── alertmanager/alertmanager.yml
    ├── otel/collector-config.yaml
    ├── grafana/provisioning/{datasources,dashboards}/*.yml
    ├── grafana/dashboards/orders.json
    ├── k8s/*.yaml
    └── tests/{__init__,test_circuit_breaker,test_retry,test_degradation}.py
```

## Open decisions resolved

- Hand-rolled resilience logic rather than `pybreaker`/`tenacity`, so the test
  suite exercises the concepts the module teaches.
- One dependency hop rather than a three-service chain, to keep the container
  count at seven. A gateway hop is the documented extension if multi-hop trace
  propagation is wanted later.
- Compose is primary; k8s is an overlay, not a replacement.
