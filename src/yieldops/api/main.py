"""FastAPI application entry point."""

import asyncio
import os

from fastapi import FastAPI, HTTPException, Query, Response

from yieldops.common.schemas import (
    AnomalyRecord,
    CostEstimate,
    CostRateCard,
    InferenceRequest,
    InferenceResponse,
    TelemetrySummary,
    WorkloadProfile,
)
from yieldops.cost.attribution import estimate_token_cost
from yieldops.evaluation.anomaly import detect_high_latency
from yieldops.inference.backend import InferenceBackend
from yieldops.inference.openai_compatible import (
    InferenceBackendError,
    OpenAICompatibleBackend,
)
from yieldops.inference.simulator import SimulatedInferenceBackend
from yieldops.telemetry.prometheus import PrometheusMetrics
from yieldops.telemetry.store import InMemoryTelemetryStore
from yieldops.workload.profiling import profile_telemetry

app = FastAPI(
    title="YieldOps",
    description="Inference operations and optimization platform",
    version="0.1.0",
)
def _configured_backend() -> InferenceBackend:
    backend_type = os.environ.get("YIELDOPS_INFERENCE_BACKEND", "simulated")
    if backend_type == "simulated":
        return SimulatedInferenceBackend()
    if backend_type == "openai_compatible":
        return OpenAICompatibleBackend.from_environment()
    raise ValueError(f"Unsupported YIELDOPS_INFERENCE_BACKEND: {backend_type}")


inference_backend: InferenceBackend = _configured_backend()
telemetry_store = InMemoryTelemetryStore()
prometheus_metrics = PrometheusMetrics()


@app.get("/health", tags=["operations"])
async def health_check() -> dict[str, str]:
    """Report whether the API process is responsive."""
    return {"status": "ok"}


@app.post("/v1/inference", response_model=InferenceResponse, tags=["inference"])
async def run_inference(request: InferenceRequest) -> InferenceResponse:
    """Run a backend without blocking the event loop; store metadata only."""
    try:
        response = await asyncio.to_thread(inference_backend.infer, request)
    except InferenceBackendError as exc:
        telemetry_store.add(exc.telemetry)
        prometheus_metrics.record(exc.telemetry)
        raise HTTPException(
            status_code=502, detail="inference backend request failed"
        ) from None
    telemetry_store.add(response.telemetry)
    prometheus_metrics.record(response.telemetry)
    return response


@app.get("/v1/telemetry/summary", response_model=TelemetrySummary, tags=["telemetry"])
async def get_telemetry_summary() -> TelemetrySummary:
    """Summarize retained request metrics with provenance counts."""
    return telemetry_store.summary()


@app.get("/metrics", include_in_schema=False)
async def get_prometheus_metrics() -> Response:
    """Export API-process metrics in Prometheus text format."""
    return Response(
        content=prometheus_metrics.render(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/v1/telemetry/profile", response_model=WorkloadProfile, tags=["telemetry"])
async def get_workload_profile() -> WorkloadProfile:
    """Profile retained requests by model and task category."""
    return profile_telemetry(telemetry_store.snapshot())


@app.get("/v1/telemetry/anomalies", response_model=list[AnomalyRecord], tags=["telemetry"])
async def get_latency_anomalies(
    window_size: int = Query(default=20, ge=3, le=500),
    threshold: float = Query(default=3.5, gt=0),
) -> list[AnomalyRecord]:
    """Apply the rolling median/MAD baseline to the retained sample."""
    return detect_high_latency(
        telemetry_store.snapshot(), window_size=window_size, threshold=threshold
    )


@app.post(
    "/v1/telemetry/cost-estimate",
    response_model=CostEstimate,
    tags=["telemetry"],
)
async def get_cost_estimate(rate_card: CostRateCard) -> CostEstimate:
    """Estimate token charges from caller-supplied rates and retained telemetry."""
    return estimate_token_cost(telemetry_store.snapshot(), rate_card)
