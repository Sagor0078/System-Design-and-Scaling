"""Chaos experiments that verify themselves.

"Break it and look at Grafana" is a demo. This is an experiment: each scenario
states a hypothesis, snapshots ``/metrics`` before and after, drives real
traffic, and then checks the deltas. The script exits non-zero if the system
did not behave as claimed, so it can run in CI as a resilience regression test.

Usage (with the stack up):

    python chaos/run_chaos.py                      # all four
    python chaos/run_chaos.py --experiment latency
    python chaos/run_chaos.py --list
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

import httpx

ORDERS_URL = "http://localhost:8000"
INVENTORY_URL = "http://localhost:8001"
INVENTORY_CONTAINER = "m4_inventory"
WARM_SKU = "widget-1"


# --------------------------------------------------------------------- parsing


def parse_metrics(text: str) -> dict[str, float]:
    """Parse Prometheus text exposition into ``{series: value}``.

    Label order is normalised so a series key is stable across scrapes --
    Prometheus makes no ordering promise, and comparing unsorted keys is a
    silent source of "metric disappeared" bugs.
    """
    out: dict[str, float] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, value = line.rpartition(" ")
        if not head:
            continue
        try:
            parsed = float(value)
        except ValueError:
            continue
        if "{" in head and head.endswith("}"):
            name, _, label_blob = head.partition("{")
            labels = _parse_labels(label_blob[:-1])
            key = name + "{" + ",".join(f'{k}="{v}"' for k, v in sorted(labels.items())) + "}"
        else:
            key = head
        out[key] = parsed
    return out


def _parse_labels(blob: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for part in blob.split('",'):
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        labels[key.strip()] = value.strip().strip('"')
    return labels


def counter_delta(
    before: dict[str, float],
    after: dict[str, float],
    name: str,
    labels: dict[str, str],
) -> float:
    """Summed increase of every series of ``name`` matching ``labels``.

    ``labels`` may be partial, so ``{"route": "/orders"}`` sums across status
    codes. A series absent from ``before`` counts from zero.
    """
    needles = [f'{k}="{v}"' for k, v in labels.items()]
    total = 0.0
    for key, value in after.items():
        series_name = key.split("{", 1)[0]
        if series_name != name:
            continue
        if not all(n in key for n in needles):
            continue
        total += value - before.get(key, 0.0)
    return total


def gauge_value(metrics: dict[str, float], name: str, labels: dict[str, str]) -> float | None:
    needles = [f'{k}="{v}"' for k, v in labels.items()]
    for key, value in metrics.items():
        if key.split("{", 1)[0] != name:
            continue
        if all(n in key for n in needles):
            return value
    return None


def verdict(assertions: list[tuple[str, bool]]) -> bool:
    """True only when there was something to check and everything held."""
    return bool(assertions) and all(ok for _label, ok in assertions)


# ----------------------------------------------------------------- driving load


async def scrape(client: httpx.AsyncClient, url: str) -> dict[str, float]:
    response = await client.get(f"{url}/metrics", timeout=10.0)
    return parse_metrics(response.text)


async def place_orders(client: httpx.AsyncClient, count: int, sku: str = WARM_SKU) -> list[int]:
    statuses: list[int] = []
    for _ in range(count):
        try:
            r = await client.post(
                f"{ORDERS_URL}/orders", json={"sku": sku, "quantity": 1}, timeout=15.0
            )
            statuses.append(r.status_code)
        except httpx.HTTPError:
            statuses.append(0)
        await asyncio.sleep(0.05)
    return statuses


async def set_chaos(client: httpx.AsyncClient, **kwargs) -> None:
    await client.post(f"{INVENTORY_URL}/chaos", json=kwargs, timeout=10.0)


async def reset_chaos(client: httpx.AsyncClient) -> None:
    try:
        await client.post(f"{INVENTORY_URL}/chaos/reset", timeout=10.0)
    except httpx.HTTPError:
        pass


async def probe(client: httpx.AsyncClient, url: str, path: str) -> int:
    try:
        return (await client.get(f"{url}{path}", timeout=10.0)).status_code
    except httpx.HTTPError:
        return 0


def docker(*args: str) -> bool:
    try:
        subprocess.run(["docker", *args], check=True, capture_output=True, timeout=60)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ------------------------------------------------------------------ experiments


@dataclass
class Experiment:
    name: str
    description: str
    hypothesis: str
    run: Callable[[httpx.AsyncClient, int], Awaitable[list[tuple[str, bool]]]] = field(repr=False)


async def warm_the_cache(client: httpx.AsyncClient) -> None:
    """A fallback can only be served if something was cached first."""
    await reset_chaos(client)
    await place_orders(client, 3)


async def exp_total_failure(client: httpx.AsyncClient, duration: int) -> list[tuple[str, bool]]:
    await warm_the_cache(client)
    before = await scrape(client, ORDERS_URL)

    await set_chaos(client, fail_rate=1.0)
    statuses = await place_orders(client, max(duration * 4, 12))
    after = await scrape(client, ORDERS_URL)
    await reset_chaos(client)

    breaker = gauge_value(after, "circuit_breaker_state", {"dependency": "inventory"})
    degraded = counter_delta(before, after, "degraded_responses_total", {"route": "/orders"})
    server_errors = sum(1 for s in statuses if s >= 500 or s == 0)

    return [
        ("breaker reached OPEN", breaker == 2.0),
        ("stale data was served", degraded > 0),
        ("no 5xx reached the client", server_errors == 0),
        ("every order was accepted", all(s in (200, 201) for s in statuses)),
    ]


async def exp_latency(client: httpx.AsyncClient, duration: int) -> list[tuple[str, bool]]:
    await warm_the_cache(client)
    before = await scrape(client, ORDERS_URL)

    # Well above REQUEST_TIMEOUT, so every call times out rather than merely slows.
    await set_chaos(client, latency_ms=3000)
    statuses = await place_orders(client, max(duration * 2, 8))
    after = await scrape(client, ORDERS_URL)
    await reset_chaos(client)

    retries = counter_delta(before, after, "retry_attempts_total", {"dependency": "inventory"})
    failures = counter_delta(before, after, "dependency_calls_total",
                             {"dependency": "inventory", "outcome": "failure"})
    degraded = counter_delta(before, after, "degraded_responses_total", {"route": "/orders"})

    return [
        ("timeouts were retried", retries > len(statuses)),
        ("calls were recorded as failures", failures > 0),
        ("stale data was served", degraded > 0),
        ("no 5xx reached the client", all(s in (200, 201) for s in statuses)),
    ]


async def exp_hard_kill(client: httpx.AsyncClient, duration: int) -> list[tuple[str, bool]]:
    await warm_the_cache(client)

    killed = docker("kill", INVENTORY_CONTAINER)
    if not killed:
        return [("docker kill succeeded", False)]

    statuses = await place_orders(client, max(duration * 2, 8))
    live = await probe(client, ORDERS_URL, "/health/live")
    ready = await probe(client, ORDERS_URL, "/health/ready")

    docker("start", INVENTORY_CONTAINER)
    await asyncio.sleep(8)
    await reset_chaos(client)

    return [
        ("orders stayed live", live == 200),
        ("orders stayed ready (warm cache)", ready == 200),
        ("orders kept accepting orders", all(s in (200, 201) for s in statuses)),
    ]


async def exp_recovery(client: httpx.AsyncClient, duration: int) -> list[tuple[str, bool]]:
    await warm_the_cache(client)

    await set_chaos(client, fail_rate=1.0)
    await place_orders(client, 12)
    opened = gauge_value(await scrape(client, ORDERS_URL), "circuit_breaker_state",
                         {"dependency": "inventory"})

    await reset_chaos(client)
    # Wait out BREAKER_RECOVERY_TIMEOUT, then probe until the breaker closes.
    closed = False
    fresh = False
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        await place_orders(client, 3)
        state = gauge_value(await scrape(client, ORDERS_URL), "circuit_breaker_state",
                            {"dependency": "inventory"})
        if state == 0.0:
            closed = True
            break
        await asyncio.sleep(2)

    if closed:
        r = await client.post(f"{ORDERS_URL}/orders",
                              json={"sku": WARM_SKU, "quantity": 1}, timeout=15.0)
        fresh = r.status_code == 201 and r.json().get("degraded") is False

    return [
        ("breaker opened under failure", opened == 2.0),
        ("breaker closed after recovery", closed),
        ("fresh data served again", fresh),
    ]


EXPERIMENTS: list[Experiment] = [
    Experiment(
        name="total_failure",
        description="inventory fails every call",
        hypothesis="breaker opens, stale stock is served, the client sees no 5xx",
        run=exp_total_failure,
    ),
    Experiment(
        name="latency",
        description="inventory responds slower than the client timeout",
        hypothesis="calls time out, are retried, then fall back to stale stock",
        run=exp_latency,
    ),
    Experiment(
        name="hard_kill",
        description="the inventory container is killed outright",
        hypothesis="orders stays live and ready while its cache is warm",
        run=exp_hard_kill,
    ),
    Experiment(
        name="recovery",
        description="inventory is restored after an outage",
        hypothesis="the breaker half-opens, closes, and fresh data flows again",
        run=exp_recovery,
    ),
]


# -------------------------------------------------------------------------- CLI


def print_report(results: list[tuple[Experiment, list[tuple[str, bool]]]]) -> bool:
    print("\n" + "=" * 72)
    print("CHAOS EXPERIMENT REPORT")
    print("=" * 72)
    all_passed = True
    for experiment, assertions in results:
        passed = verdict(assertions)
        all_passed = all_passed and passed
        print(f"\n[{'PASS' if passed else 'FAIL'}] {experiment.name} — {experiment.description}")
        print(f"       hypothesis: {experiment.hypothesis}")
        if not assertions:
            print("       (no assertions ran)")
        for label, ok in assertions:
            print(f"       {'ok  ' if ok else 'FAIL'}  {label}")
    print("\n" + "=" * 72)
    print(f"RESULT: {'all experiments passed' if all_passed else 'one or more experiments FAILED'}")
    print("=" * 72 + "\n")
    return all_passed


async def main_async(names: list[str], duration: int) -> int:
    chosen = [e for e in EXPERIMENTS if e.name in names]
    results = []
    async with httpx.AsyncClient() as client:
        if await probe(client, ORDERS_URL, "/health/live") != 200:
            print(f"orders is not reachable at {ORDERS_URL} — is the stack up?",
                  file=sys.stderr)
            return 2
        for experiment in chosen:
            print(f"\n>>> running {experiment.name}: {experiment.description}")
            try:
                results.append((experiment, await experiment.run(client, duration)))
            except Exception as exc:  # noqa: BLE001 - report, never crash mid-run
                results.append((experiment, [(f"experiment raised {exc!r}", False)]))
            await reset_chaos(client)
    return 0 if print_report(results) else 1


def main(argv: list[str] | None = None) -> int:
    global ORDERS_URL, INVENTORY_URL

    parser = argparse.ArgumentParser(description="Module 4 chaos experiments")
    parser.add_argument("--experiment", action="append", dest="experiments",
                        choices=[e.name for e in EXPERIMENTS],
                        help="run only this experiment (repeatable)")
    parser.add_argument("--duration", type=int, default=5,
                        help="rough seconds of load per experiment (default: 5)")
    parser.add_argument("--orders-url", default="http://localhost:8000")
    parser.add_argument("--inventory-url", default="http://localhost:8001")
    parser.add_argument("--list", action="store_true", help="list experiments and exit")
    args = parser.parse_args(argv)

    ORDERS_URL = args.orders_url
    INVENTORY_URL = args.inventory_url

    if args.list:
        for e in EXPERIMENTS:
            print(f"{e.name:<14} {e.description}\n{'':<15}hypothesis: {e.hypothesis}")
        return 0

    names = args.experiments or [e.name for e in EXPERIMENTS]
    return asyncio.run(main_async(names, args.duration))


if __name__ == "__main__":
    raise SystemExit(main())
