"""The orders service.

Survives a failing inventory dependency, and exposes how: Prometheus metrics on
``/metrics``, OTLP traces of every retry and rejection, JSON logs carrying the
trace id, and two probe endpoints with deliberately different meanings.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from observability import metrics
from observability.logging import configure_logging
from observability.otel import setup_tracing
from resilience import NoFallbackAvailable

from orders.clients import InventoryClient
from orders.config import Settings

settings = Settings.from_env()
configure_logging(settings.service_name)
log = logging.getLogger("orders")

#: Demo store. Module 2 is where persistence lives; this module is about staying
#: up when a dependency does not.
ORDERS: dict[str, dict[str, Any]] = {}


class CreateOrder(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tests inject their own client before startup; never clobber it.
    if getattr(app.state, "inventory", None) is None:
        app.state.inventory = InventoryClient(settings)
    yield
    await app.state.inventory.aclose()


app = FastAPI(title="Orders Service", version="1.0.0", lifespan=lifespan)
app.state.inventory = None
setup_tracing(settings.service_name, app)


def inventory(request: Request) -> InventoryClient:
    return request.app.state.inventory


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


@app.post("/orders")
async def create_order(payload: CreateOrder, request: Request, response: Response):
    try:
        stock = await inventory(request).get_stock(payload.sku)
    except NoFallbackAvailable:
        # Honest 503: we do not know the stock level and have never known it.
        log.error("rejecting order: inventory unavailable and no cached stock",
                  extra={"sku": payload.sku})
        raise HTTPException(
            status_code=503,
            detail="inventory unavailable and no cached stock for this SKU",
        )

    order_id = uuid.uuid4().hex[:12]
    record = {
        "order_id": order_id,
        "sku": payload.sku,
        "quantity": payload.quantity,
        "available_qty": stock.value.get("qty"),
        "degraded": stock.stale,
        "stale_age_seconds": round(stock.age_seconds, 3),
        "status": "accepted_degraded" if stock.stale else "accepted",
    }
    ORDERS[order_id] = record

    if stock.stale:
        metrics.record_degraded("/orders")
        log.warning("order accepted on stale stock data",
                    extra={"sku": payload.sku, "age_seconds": stock.age_seconds})
        response.status_code = 200
    else:
        response.status_code = 201
    return record


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    record = ORDERS.get(order_id)
    if record is None:
        raise HTTPException(status_code=404, detail="order not found")
    return record


@app.get("/health/live")
async def live():
    """Is the process healthy?

    Deliberately dependency-free. If liveness consulted inventory, an inventory
    outage would make Kubernetes restart every orders pod -- turning a degraded
    system into a dead one, and losing the warm cache that was keeping it alive.
    """
    return {"status": "alive", "service": settings.service_name}


@app.get("/health/ready")
async def ready(request: Request):
    """Should this instance receive traffic?

    Red only when the breaker is open *and* the cache is cold, i.e. when every
    request would fail. Degraded-but-serving stays green.
    """
    client = inventory(request)
    if client is None or not client.ready():
        raise HTTPException(status_code=503, detail="inventory unavailable, cache cold")
    return {
        "status": "ready",
        "service": settings.service_name,
        "breaker": str(client.breaker.state),
    }


@app.get("/metrics")
async def prometheus_metrics():
    body, content_type = metrics.render()
    return Response(content=body, media_type=content_type)
