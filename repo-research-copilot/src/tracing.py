from __future__ import annotations

import logging

from fastapi import FastAPI

from src.settings import Settings

_configured = False


def configure_tracing(app: FastAPI, settings: Settings) -> bool:
    global _configured
    if _configured or not settings.tracing_enabled:
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    except Exception:
        logging.getLogger("repo_research.api").exception(
            "tracing_dependencies_not_available"
        )
        return False

    resource = Resource.create({"service.name": settings.tracing_service_name})
    provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(TraceIdRatioBased(settings.otel_sampler_ratio)),
    )

    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    else:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    _configured = True
    logging.getLogger("repo_research.api").info("tracing_enabled")
    return True
