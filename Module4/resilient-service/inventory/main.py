"""The dependency you break.

A deliberately unreliable stock service. ``POST /chaos`` injects a failure rate,
added latency, or a hard outage; the orders service is expected to survive all
three. Stock quantities are derived from a hash of the SKU so repeated calls
agree, which means a stale cached value can be compared against the live one.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import random
import time
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from observability import metrics
from observability.logging import configure_logging
from observability.otel import setup_tracing

SERVICE_NAME = os.getenv("SERVICE_NAME", "inventory")

configure_logging(SERVICE_NAME)
log = logging.getLogger("inventory")


def stock_for(sku: str) -> int:
    """A stable pseudo-quantity for a SKU, in [0, 499]."""
    digest = hashlib.sha256(sku.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % 500


@dataclass
class ChaosState:
    """The injected-fault configuration, clamped to sane ranges."""

    fail_rate: float = 0.0
    latency_ms: int = 0
    down: bool = False
    _rng: random.Random = field(default_factory=random.Random, repr=False)

    def __post_init__(self) -> None:
        self._clamp()

    def _clamp(self) -> None:
        self.fail_rate = min(1.0, max(0.0, float(self.fail_rate)))
        self.latency_ms = max(0, int(self.latency_ms))
        self.down = bool(self.down)

    def apply(
        self,
        fail_rate: float | None = None,
        latency_ms: int | None = None,
        down: bool | None = None,
    ) -> None:
        if fail_rate is not None:
            self.fail_rate = fail_rate
        if latency_ms is not None:
            self.latency_ms = latency_ms
        if down is not None:
            self.down = down
        self._clamp()

    def reset(self) -> None:
        self.fail_rate = 0.0
        self.latency_ms = 0
        self.down = False

    def should_fail(self, rng: random.Random | None = None) -> bool:
        """Roll for failure. The 0.0 and 1.0 boundaries are exact, not sampled."""
        if self.fail_rate <= 0.0:
            return False
        if self.fail_rate >= 1.0:
            return True
        return (rng or self._rng).random() < self.fail_rate

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "fail_rate": self.fail_rate,
            "latency_ms": self.latency_ms,
            "down": self.down,
        }


class ChaosRequest(BaseModel):
    fail_rate: float | None = Field(default=None, description="0.0-1.0, clamped")
    latency_ms: int | None = Field(default=None, description="added delay, >= 0")
    down: bool | None = Field(default=None, description="return 503 for every call")


chaos = ChaosState()

app = FastAPI(title="Inventory Service", version="1.0.0")
setup_tracing(SERVICE_NAME, app)


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        metrics.observe_request(
            route=metrics.route_label(request),
            method=request.method,
            status=500,
            duration=time.perf_counter() - started,
        )
        raise
    metrics.observe_request(
        route=metrics.route_label(request),
        method=request.method,
        status=response.status_code,
        duration=time.perf_counter() - started,
    )
    return response


@app.get("/stock/{sku}")
async def get_stock(sku: str):
    if chaos.down:
        log.warning("rejecting call: chaos down", extra={"sku": sku})
        return JSONResponse(
            status_code=503, content={"error": "inventory unavailable"}
        )

    if chaos.latency_ms:
        await asyncio.sleep(chaos.latency_ms / 1000.0)

    if chaos.should_fail():
        log.warning("injected failure", extra={"sku": sku, "fail_rate": chaos.fail_rate})
        return JSONResponse(
            status_code=500, content={"error": "injected inventory failure"}
        )

    return {"sku": sku, "qty": stock_for(sku), "source": "inventory"}


@app.post("/chaos")
async def set_chaos(req: ChaosRequest):
    chaos.apply(fail_rate=req.fail_rate, latency_ms=req.latency_ms, down=req.down)
    log.info("chaos updated", extra=chaos.as_dict())
    return chaos.as_dict()


@app.get("/chaos")
async def get_chaos():
    return chaos.as_dict()


@app.post("/chaos/reset")
async def reset_chaos():
    chaos.reset()
    log.info("chaos reset")
    return chaos.as_dict()


@app.get("/health/live")
async def live():
    # Liveness says "the process works", nothing more. Injected chaos is a
    # deliberate state, not a reason for the orchestrator to restart us.
    return {"status": "alive", "service": SERVICE_NAME}


@app.get("/health/ready")
async def ready():
    if chaos.down:
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "reason": "chaos: down"}
        )
    return {"status": "ready", "service": SERVICE_NAME}


@app.get("/metrics")
async def prometheus_metrics():
    body, content_type = metrics.render()
    return Response(content=body, media_type=content_type)
