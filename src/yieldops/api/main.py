"""FastAPI application entry point."""

from fastapi import FastAPI
from yieldops.common.schemas import InferenceRequest, InferenceResponse, TelemetrySummary
from yieldops.inference.simulator import SimulatedInferenceBackend
from yieldops.telemetry.store import InMemoryTelemetryStore

app = FastAPI(
    title="YieldOps",
    description="Inference operations and optimization platform",
    version="0.1.0",
)
inference_backend = SimulatedInferenceBackend()
telemetry_store = InMemoryTelemetryStore()


@app.get("/health", tags=["operations"])
async def health_check() -> dict[str, str]:
    """Report whether the API process is responsive."""
    return {"status": "ok"}


@app.post("/v1/inference", response_model=InferenceResponse, tags=["inference"])
async def run_inference(request: InferenceRequest) -> InferenceResponse:
    """Return a synthetic completion and record prompt-free telemetry."""
    response = inference_backend.infer(request)
    telemetry_store.add(response.telemetry)
    return response


@app.get("/v1/telemetry/summary", response_model=TelemetrySummary, tags=["telemetry"])
async def get_telemetry_summary() -> TelemetrySummary:
    """Summarize in-memory request metrics; values remain labeled simulated."""
    return telemetry_store.summary()
