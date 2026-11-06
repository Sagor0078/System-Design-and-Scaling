# Resilient Service — Reliability, Observability & Fault Tolerance

A containerised demo of a service that **survives a failing dependency and shows
you why**. The `orders` service calls an `inventory` service that you can break
on demand; orders answers with a circuit breaker, bounded retries, timeouts, and
a stale-data fallback, while Prometheus, Grafana, Jaeger and Alertmanager make
every one of those decisions visible.

The chaos experiments verify themselves: each one asserts on metric deltas and
exits non-zero if the system did not behave as claimed.

---

## Architecture

```
                        ┌──────────────────────────────────────────┐
   client ──▶  orders :8000  ──timeout → retry → breaker → fallback──▶  inventory :8001
                        │     │                                      (/chaos: fail_rate,
                        │     │                                       latency_ms, down)
          /metrics ◀────┘     └────OTLP────▶  otel-collector  ──▶  jaeger :16686
               ▲
               │ scrape (5s)
        prometheus :9090  ──alerts──▶  alertmanager :9093
               │
               └──▶  grafana :3000   (provisioned datasource + dashboard)
```

`orders` is the system under test. `inventory` is the dependency you break.
Everything else is the observability plane.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker & Docker Compose | ≥ 24.x / Compose V2 |
| Python (for the tests and the chaos CLI) | ≥ 3.12 |

---

## Quick Start

### 1. Start the stack

```bash
cd Module4/fault-tolerance-system
docker compose up -d --build
```

Seven containers come up. Wait for health:

```bash
docker compose ps
```

### 2. Generate some traffic

```bash
for i in $(seq 1 20); do
  curl -s -X POST localhost:8000/orders \
    -H 'Content-Type: application/json' \
    -d '{"sku":"widget-1","quantity":2}' > /dev/null
done
```

### 3. Open the consoles

| What | URL | Notes |
|------|-----|-------|
| Grafana dashboard | http://localhost:3000 | anonymous viewer; dashboard "Module 4 — Orders Reliability" |
| Prometheus | http://localhost:9090 | try `circuit_breaker_state` |
| Alerts | http://localhost:9090/alerts | rule state |
| Alertmanager | http://localhost:9093 | grouped alerts |
| Jaeger | http://localhost:16686 | service `orders`, look at a degraded request |
| Raw metrics | http://localhost:8000/metrics | what Prometheus scrapes |

### 4. Break it

```bash
# every inventory call now fails
curl -s -X POST localhost:8001/chaos -H 'Content-Type: application/json' \
  -d '{"fail_rate": 1.0}'

# keep ordering — these still succeed, flagged degraded
curl -s -X POST localhost:8000/orders -H 'Content-Type: application/json' \
  -d '{"sku":"widget-1","quantity":1}' | python3 -m json.tool

# put it back
curl -s -X POST localhost:8001/chaos/reset
```

### 5. Run the chaos experiments

```bash
pip install -r requirements.txt     # httpx, for the harness
python chaos/run_chaos.py           # all four, with a pass/fail report
python chaos/run_chaos.py --experiment latency
python chaos/run_chaos.py --list
```

---

## Chaos runbook

| Experiment | What it does | Expected observation |
|------------|--------------|----------------------|
| `total_failure` | `fail_rate=1.0` on inventory | Breaker gauge climbs to `2` (OPEN), `degraded_responses_total` rises, **client sees zero 5xx**, Grafana's breaker timeline turns red |
| `latency` | `latency_ms=3000`, above the 1s client timeout | `retry_attempts_total` outruns the request count, p95 spikes then falls as the breaker opens, traces show three attempt spans then a rejection |
| `hard_kill` | `docker kill m4_inventory` | `/health/live` stays 200, `/health/ready` stays 200 (warm cache), orders keep being accepted |
| `recovery` | reset chaos, keep calling | Breaker goes OPEN → HALF-OPEN → CLOSED, `degraded` stops, fresh data returns with `degraded: false` |

Each experiment snapshots `/metrics` before and after and prints an assertion
table, so "it worked" is a measurement rather than an impression.

---

## Endpoints

### orders (`:8000`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/orders` | Create an order. `201` fresh, `200` + `degraded: true` on stale data, `503` when inventory is unusable and nothing is cached |
| GET | `/orders/{order_id}` | Fetch an order |
| GET | `/health/live` | Liveness — process only, **never** checks dependencies |
| GET | `/health/ready` | Readiness — `503` only when the breaker is open *and* the cache is cold |
| GET | `/metrics` | Prometheus exposition |

### inventory (`:8001`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/stock/{sku}` | Stock level (stable per SKU) |
| POST | `/chaos` | `{"fail_rate": 0.0-1.0, "latency_ms": int, "down": bool}` — any subset |
| GET | `/chaos` | Current chaos state |
| POST | `/chaos/reset` | Back to healthy |
| GET | `/health/live`, `/health/ready`, `/metrics` | as above |

---

## Project structure

```
fault-tolerance-system/
├── docker-compose.yml              # seven services
├── Dockerfile                      # one image, both Python services
├── requirements.txt
├── conftest.py                     # anyio backend + import path
├── resilience/                     # ← the teaching core, stdlib only
│   ├── circuit_breaker.py          # CLOSED / OPEN / HALF_OPEN, injected clock
│   ├── retry.py                    # exponential backoff + full jitter
│   └── degradation.py              # last-known-good cache
├── orders/
│   ├── config.py                   # env-driven Settings
│   ├── clients.py                  # breaker → retry → timeout → fallback
│   └── main.py                     # FastAPI app, probes, /metrics
├── inventory/main.py               # the dependency, with /chaos
├── observability/
│   ├── metrics.py                  # Prometheus collectors
│   ├── logging.py                  # JSON logs with trace_id
│   └── otel.py                     # OTLP tracing, best-effort
├── chaos/run_chaos.py              # four self-verifying experiments
├── prometheus/{prometheus.yml,alert_rules.yml}
├── alertmanager/alertmanager.yml
├── otel/collector-config.yaml
├── grafana/{provisioning,dashboards}/
├── k8s/                            # probes, HPA, PDB, kustomization
└── tests/                          # 82 tests, no containers required
```

---

## How it works

### The layer order is the lesson

`orders/clients.py` composes four things, and the order matters more than the
code:

1. **Breaker** — if inventory is known-bad, do not even start the call.
2. **Retry** — a single transient blip should never reach the user.
3. **Timeout** — a hung call must not occupy a worker indefinitely.
4. **Fallback** — if all of the above failed, serve the last known stock level
   and label it stale.

Two classic ways to get this wrong:

- **Retry outside the breaker** multiplies the load on a dying dependency by the
  attempt count. The breaker exists to *reduce* pressure; wrapping it in retries
  inverts that.
- **A breaker without a timeout** never trips, because the calls never finish
  failing. It just accumulates stuck workers.

### Full jitter, not plain exponential backoff

Plain exponential backoff synchronises clients: everyone who failed at the same
moment retries at the same moment. `retry.py` draws uniformly from `[0, cap]`
instead, so a thundering herd becomes a spread.

### Why liveness ignores dependencies

`/health/live` reports only whether the process works. If it checked inventory,
an inventory outage would fail liveness on **every** orders pod, Kubernetes
would restart them all, and the restart would wipe the warm cache that was the
only thing still serving customers. A dependency outage would become a
self-inflicted outage.

`/health/ready` is allowed to consult the breaker, but it only goes red when the
breaker is open **and** the cache is cold — i.e. when this pod genuinely cannot
answer. Degraded-but-serving stays in rotation.

### Degradation that tells the truth

A cold cache raises rather than returning an empty value. "No stock recorded"
and "we cannot reach inventory" must not look the same to the caller, so the
first becomes a `200` with `qty: 0` and the second a `503`. When a stale value
*is* available, the response says `degraded: true` and reports
`stale_age_seconds`, and the caller can decide what that is worth.

### Metrics

| Metric | Type | Meaning |
|--------|------|---------|
| `http_requests_total{route,method,status}` | counter | requests served |
| `http_request_duration_seconds{route,method}` | histogram | latency, source of the p50/p95/p99 panels |
| `circuit_breaker_state{dependency}` | gauge | `0` closed, `1` half-open, `2` open |
| `dependency_calls_total{dependency,outcome}` | counter | `success`, `failure`, `circuit_open`, `degraded`, `no_fallback` |
| `retry_attempts_total{dependency}` | counter | attempts, including the first |
| `degraded_responses_total{route}` | counter | responses served from stale cache |

Route labels come from the matched route *template* (`/orders/{order_id}`),
never the raw path, and anything unmatched collapses to a single `unmatched`
label. Raw paths would mint a time series per order id, and a vulnerability
scanner walking 10,000 URLs would permanently bloat the Prometheus index.

### Dashboard colors

The categorical palette was checked with a contrast/CVD validator rather than
chosen by eye: every adjacent pair clears deuteranopia, protanopia and
tritanopia separation as well as a normal-vision floor, in both light and dark
mode. Breaker states use reserved status colors **with text labels**, so state
is never conveyed by color alone. Latency quantiles share one hue light-to-dark
because p50/p95/p99 are ordered magnitudes, not separate identities — and they
share one axis, because a second y-axis is how dashboards start lying.

---

## Kubernetes

```bash
# build the image into your local cluster (kind shown; minikube: minikube image load)
docker build -t module4/fault-tolerance-system:local .
kind load docker-image module4/fault-tolerance-system:local

kubectl apply -k k8s/
kubectl -n module4 get pods,hpa

kubectl -n module4 port-forward svc/orders 8000:8000
```

What the overlay demonstrates:

- **Distinct probes** — `startupProbe` for slow boots, `livenessProbe` on
  `/health/live`, `readinessProbe` on `/health/ready`.
- **Autoscaling** — HPA on CPU at 60% utilisation, 2→6 replicas. The CPU
  *requests* in the Deployment are not optional: without them there is no
  denominator for utilisation and the HPA silently never fires.
- **Disruption budget** — at least one orders pod stays up during drains.
- **Scrape annotations** — enough for a plain Prometheus. With
  kube-prometheus-stack, replace them with a `ServiceMonitor` selecting
  `app: orders` on port `http`, path `/metrics`.

Chaos on a cluster: `kubectl -n module4 delete pod -l app=inventory` instead of
`docker kill`, and watch `/health/ready` on orders stay green while the cache is
warm.

---

## Tests

```bash
pip install -r requirements.txt
python -m pytest -q          # 82 tests, no containers, no sleeps
```

The `resilience/` package imports only the standard library, which is what makes
this possible: the breaker's clock, the retry's sleep and RNG, and the cache's
clock are all injected, so every state transition is exercised deterministically
in milliseconds.

---

## Teardown

```bash
docker compose down -v       # -v also drops Prometheus and Grafana volumes
kubectl delete -k k8s/       # if you deployed to a cluster
```

---

## Extending this demo

| Use case | How |
|----------|-----|
| **Cascading failure** | Add a `gateway` service in front of orders and watch containment across two hops in Jaeger |
| **Bulkheads** | Give the inventory client its own bounded connection pool and semaphore, then show one slow dependency not starving the rest |
| **Load shedding** | Reject low-priority requests above a concurrency watermark instead of queueing them |
| **Real alerting** | Swap Alertmanager's `null` receiver for a Slack or webhook receiver |
| **SLOs** | Add a multi-window burn-rate alert over `http_requests_total` |
| **Trace-based tests** | Assert on span structure from the collector rather than on metrics |
