"""Framework-free resilience primitives.

Standard library only, on purpose: these are the pieces Module 4 teaches, and
keeping HTTP, FastAPI and Prometheus out of here is what makes them unit
testable in milliseconds.
"""

from resilience.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from resilience.degradation import Fallback, NoFallbackAvailable, StaleCache
from resilience.retry import RetryPolicy

__all__ = [
    "CircuitBreaker",
    "CircuitOpenError",
    "CircuitState",
    "Fallback",
    "NoFallbackAvailable",
    "RetryPolicy",
    "StaleCache",
]
