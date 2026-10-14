"""Environment-driven settings for the orders service.

Frozen so nothing mutates configuration at runtime, and constructible directly
in tests without touching the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    inventory_url: str = "http://inventory:8001"
    request_timeout: float = 1.0

    breaker_failure_threshold: int = 5
    breaker_recovery_timeout: float = 15.0
    breaker_half_open_max_calls: int = 1
    breaker_success_threshold: int = 2

    retry_max_attempts: int = 3
    retry_base_delay: float = 0.05
    retry_max_delay: float = 0.5

    cache_ttl: float = 30.0

    service_name: str = "orders"
    otlp_endpoint: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            inventory_url=os.getenv("INVENTORY_URL", cls.inventory_url),
            request_timeout=_env_float("REQUEST_TIMEOUT", cls.request_timeout),
            breaker_failure_threshold=_env_int(
                "BREAKER_FAILURE_THRESHOLD", cls.breaker_failure_threshold
            ),
            breaker_recovery_timeout=_env_float(
                "BREAKER_RECOVERY_TIMEOUT", cls.breaker_recovery_timeout
            ),
            breaker_half_open_max_calls=_env_int(
                "BREAKER_HALF_OPEN_MAX_CALLS", cls.breaker_half_open_max_calls
            ),
            breaker_success_threshold=_env_int(
                "BREAKER_SUCCESS_THRESHOLD", cls.breaker_success_threshold
            ),
            retry_max_attempts=_env_int("RETRY_MAX_ATTEMPTS", cls.retry_max_attempts),
            retry_base_delay=_env_float("RETRY_BASE_DELAY", cls.retry_base_delay),
            retry_max_delay=_env_float("RETRY_MAX_DELAY", cls.retry_max_delay),
            cache_ttl=_env_float("CACHE_TTL", cls.cache_ttl),
            service_name=os.getenv("SERVICE_NAME", cls.service_name),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        )
