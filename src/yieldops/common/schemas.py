"""Validated request, response, and telemetry contracts."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MetricProvenance(StrEnum):
    """How a metric was obtained; this must travel with derived results."""

    SIMULATED = "simulated"
    MEASURED = "measured"
    ESTIMATED = "estimated"


class TaskCategory(StrEnum):
    """General workload classes used for slicing evaluation results."""

    EXTRACTION = "structured_extraction"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    OTHER = "other"


class InferenceRequest(BaseModel):
    """Input accepted by the inference API; prompt content is not telemetry."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1, max_length=16_000)
    model_name: str = Field(default="yieldops-simulator", min_length=1, max_length=128)
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    task_category: TaskCategory = TaskCategory.OTHER
    max_output_tokens: int = Field(default=16, ge=1, le=2_048)


class InferenceTelemetry(BaseModel):
    """Request-level performance metadata without prompt or output contents."""

    request_id: UUID
    timestamp_utc: datetime
    model_name: str
    tenant_id: str | None
    task_category: TaskCategory
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    ttft_ms: float = Field(ge=0)
    tpot_ms: float = Field(ge=0)
    end_to_end_latency_ms: float = Field(ge=0)
    success: bool
    provenance: MetricProvenance


class InferenceResponse(BaseModel):
    request_id: UUID
    model_name: str
    output: str
    telemetry: InferenceTelemetry


class TelemetrySummary(BaseModel):
    request_count: int = Field(ge=0)
    simulated_request_count: int = Field(ge=0)
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    p50_end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    p95_end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    p99_end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    provenance: MetricProvenance = MetricProvenance.SIMULATED
