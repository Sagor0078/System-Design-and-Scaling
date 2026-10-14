"""The inventory client: where the resilience primitives are composed.

The order of the layers is the whole lesson, outermost first:

1. **Breaker** -- if the dependency is known-bad, do not even start.
2. **Retry** -- a single transient blip should not reach the user.
3. **Timeout** -- a hung call must not occupy a worker indefinitely.
4. **Fallback** -- if all of that failed, serve the last known value and say so.

Getting this order wrong is the classic mistake. Retry *outside* the breaker
multiplies load on a dying dependency by the attempt count, and a breaker
without a timeout never trips because the calls never finish.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from observability import metrics
from resilience import (
    CircuitBreaker,
    CircuitOpenError,
    Fallback,
    NoFallbackAvailable,
    RetryPolicy,
    StaleCache,
)

from orders.config import Settings

log = logging.getLogger("orders.inventory")

DEPENDENCY = "inventory"


class DependencyError(RuntimeError):
    """The dependency failed in a way worth retrying (5xx, timeout, refused)."""


class BadRequest(RuntimeError):
    """The dependency rejected our request (4xx). Retrying cannot help."""


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, DependencyError)


class InventoryClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._http = httpx.AsyncClient(
            base_url=settings.inventory_url,
            timeout=settings.request_timeout,
            transport=transport,
        )
        self.cache = StaleCache(ttl=settings.cache_ttl)
        self.breaker = CircuitBreaker(
            DEPENDENCY,
            failure_threshold=settings.breaker_failure_threshold,
            recovery_timeout=settings.breaker_recovery_timeout,
            half_open_max_calls=settings.breaker_half_open_max_calls,
            success_threshold=settings.breaker_success_threshold,
        )
        self.breaker.on_state_change = self._on_breaker_change
        metrics.set_breaker_state(DEPENDENCY, self.breaker.state)

        self.retry = RetryPolicy(
            max_attempts=settings.retry_max_attempts,
            base_delay=settings.retry_base_delay,
            max_delay=settings.retry_max_delay,
            retryable=_is_retryable,
        )
        self.retry.on_attempt = lambda _attempt: metrics.record_retry_attempt(DEPENDENCY)

    # --------------------------------------------------------------- internals

    def _on_breaker_change(self, name: str, state) -> None:
        metrics.set_breaker_state(name, state)
        log.warning("circuit breaker state change", extra={"dependency": name, "state": str(state)})

    async def fetch_once(self, sku: str) -> dict:
        """One HTTP call, with transport and status errors classified."""
        try:
            response = await self._http.get(f"/stock/{sku}")
        except httpx.TimeoutException as exc:
            raise DependencyError(f"inventory timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise DependencyError(f"inventory unreachable: {exc}") from exc

        if response.status_code >= 500:
            raise DependencyError(f"inventory returned {response.status_code}")
        if response.status_code >= 400:
            raise BadRequest(f"inventory returned {response.status_code}")
        return response.json()

    async def _fetch_with_retry(self, sku: str) -> dict:
        """RetryPolicy's schedule, awaited.

        The policy owns the attempt count, the retryable predicate and the
        jittered delays; only the sleep is async here.
        """
        for attempt in range(1, self.retry.max_attempts + 1):
            if self.retry.on_attempt is not None:
                self.retry.on_attempt(attempt)
            try:
                return await self.fetch_once(sku)
            except BaseException as exc:
                if attempt == self.retry.max_attempts or not self.retry.retryable(exc):
                    raise
                await asyncio.sleep(self.retry.delay_for(attempt))
        raise AssertionError("unreachable")  # pragma: no cover

    # ------------------------------------------------------------------ public

    async def get_stock(self, sku: str) -> Fallback:
        """Current stock, or the last known value marked stale.

        Raises :class:`NoFallbackAvailable` when the dependency is unusable and
        nothing was ever cached for this SKU -- the caller must surface that as
        a 503 rather than pretend the stock is zero.
        """
        try:
            is_probe = self.breaker.acquire()
        except CircuitOpenError:
            metrics.record_dependency_call(DEPENDENCY, "circuit_open")
            return self._fallback(sku)

        try:
            payload = await self._fetch_with_retry(sku)
        except BaseException as exc:
            self.breaker.record_failure(is_probe)
            metrics.record_dependency_call(DEPENDENCY, "failure")
            log.warning("inventory call failed", extra={"sku": sku, "error": str(exc)})
            return self._fallback(sku)

        self.breaker.record_success(is_probe)
        metrics.record_dependency_call(DEPENDENCY, "success")
        self.cache.put(sku, payload)
        return Fallback(value=payload, stale=False, age_seconds=0.0)

    def _fallback(self, sku: str) -> Fallback:
        try:
            stale = self.cache.fallback(sku)
        except NoFallbackAvailable:
            metrics.record_dependency_call(DEPENDENCY, "no_fallback")
            raise
        metrics.record_dependency_call(DEPENDENCY, "degraded")
        return stale

    def ready(self) -> bool:
        """Can this instance still serve traffic?

        Open breaker plus an empty cache means no, every request would 503.
        Open breaker with a warm cache means yes -- degraded service is still
        service, and removing the pod from rotation would help nobody.
        """
        from resilience import CircuitState

        if self.breaker.state is CircuitState.OPEN and len(self.cache) == 0:
            return False
        return True

    async def aclose(self) -> None:
        await self._http.aclose()
