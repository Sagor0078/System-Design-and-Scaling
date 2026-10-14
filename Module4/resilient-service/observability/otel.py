"""OpenTelemetry tracing setup.

Everything here is best-effort by design. A collector that is down, a missing
SDK, a bad endpoint -- none of those may take the service with them, so the
whole body is guarded and failures are logged once and shrugged off. Tracing is
how you debug an outage; it must not be able to cause one.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

_configured = False


def setup_tracing(service_name: str, app: object | None = None) -> bool:
    """Wire up OTLP tracing and instrument FastAPI/httpx.

    Returns True when tracing is live, False when it was skipped. Never raises.
    """
    global _configured
    if _configured:
        return True

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        log.info("tracing disabled: OTEL_EXPORTER_OTLP_ENDPOINT is unset")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(
            resource=Resource.create({"service.name": service_name})
        )
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
        trace.set_tracer_provider(provider)

        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()

        if app is not None:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)

        _configured = True
        log.info("tracing enabled", extra={"otlp_endpoint": endpoint})
        return True
    except Exception as exc:  # noqa: BLE001 - telemetry must never break serving
        log.warning("tracing setup failed; continuing without traces: %s", exc)
        return False


def tracer(name: str):
    """A tracer, or a no-op stand-in when the SDK is absent."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except Exception:  # noqa: BLE001 # pragma: no cover
        return _NoopTracer()


class _NoopTracer:  # pragma: no cover
    class _Span:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def set_attribute(self, *_a, **_k):
            return None

    def start_as_current_span(self, *_a, **_k):
        return self._Span()
