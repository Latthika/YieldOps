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
    temperature: float = Field(default=0.2, ge=0, le=2)
    top_p: float = Field(default=1.0, gt=0, le=1)


class InferenceTelemetry(BaseModel):
    """Request-level performance metadata without prompt or output contents."""

    request_id: UUID
    timestamp_utc: datetime
    model_name: str
    tenant_id: str | None
    task_category: TaskCategory
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    token_count_provenance: MetricProvenance | None = None
    ttft_ms: float | None = Field(default=None, ge=0)
    tpot_ms: float | None = Field(default=None, ge=0)
    end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    output_tokens_per_second: float | None = Field(default=None, ge=0)
    success: bool
    provenance: MetricProvenance
    error_type: str | None = None


class InferenceResponse(BaseModel):
    request_id: UUID
    model_name: str
    output: str
    telemetry: InferenceTelemetry


class TelemetrySummary(BaseModel):
    request_count: int = Field(ge=0)
    successful_request_count: int = Field(ge=0)
    failed_request_count: int = Field(ge=0)
    simulated_request_count: int = Field(ge=0)
    measured_request_count: int = Field(ge=0)
    estimated_request_count: int = Field(ge=0)
    requests_without_token_counts: int = Field(ge=0)
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    p50_end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    p95_end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    p99_end_to_end_latency_ms: float | None = Field(default=None, ge=0)
    provenance: MetricProvenance | None = None


class ModelTokenRates(BaseModel):
    """User-supplied provider prices; values are USD per 1,000 tokens."""

    input_usd_per_1k_tokens: float = Field(ge=0)
    output_usd_per_1k_tokens: float = Field(ge=0)


class CostRateCard(BaseModel):
    """Configurable rates keyed by the model label recorded on requests."""

    rates_by_model: dict[str, ModelTokenRates]


class CostEstimate(BaseModel):
    provenance: MetricProvenance = MetricProvenance.ESTIMATED
    currency: str = "USD"
    formula: str
    priced_request_count: int = Field(ge=0)
    unpriced_request_count: int = Field(ge=0)
    total_estimated_cost_usd: float = Field(ge=0)
    mean_estimated_cost_per_priced_request_usd: float | None = Field(default=None, ge=0)
    by_model_usd: dict[str, float]
    by_task_category_usd: dict[str, float]
    by_tenant_usd: dict[str, float]
    configured_rates_by_model: dict[str, ModelTokenRates]


class WorkloadGroupSummary(BaseModel):
    group: str
    request_count: int = Field(ge=0)
    successful_request_count: int = Field(ge=0)
    failed_request_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    requests_without_token_counts: int = Field(ge=0)
    p50_latency_ms: float | None = Field(default=None, ge=0)
    p95_latency_ms: float | None = Field(default=None, ge=0)
    p99_latency_ms: float | None = Field(default=None, ge=0)
    output_tokens_per_second: float | None = Field(default=None, ge=0)


class WorkloadProfile(BaseModel):
    provenance_counts: dict[str, int]
    request_count: int = Field(ge=0)
    successful_request_count: int = Field(ge=0)
    failed_request_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    requests_without_token_counts: int = Field(ge=0)
    traffic_span_seconds: float | None = Field(default=None, ge=0)
    requests_per_second: float | None = Field(default=None, ge=0)
    output_tokens_per_second: float | None = Field(default=None, ge=0)
    peak_requests_per_minute: int = Field(default=0, ge=0)
    peak_minute_utc: datetime | None = None
    per_minute_request_counts: dict[str, int]
    by_model: list[WorkloadGroupSummary]
    by_task_category: list[WorkloadGroupSummary]


class AnomalyRecord(BaseModel):
    request_id: UUID
    timestamp_utc: datetime
    observed_latency_ms: float = Field(ge=0)
    baseline_median_ms: float = Field(ge=0)
    robust_z_score: float = Field(ge=0)
    provenance: MetricProvenance
