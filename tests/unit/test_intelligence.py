"""Tests for cost attribution, workload profiles, and anomaly baselines."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from yieldops.common.schemas import (
    CostRateCard,
    InferenceTelemetry,
    MetricProvenance,
    ModelTokenRates,
    TaskCategory,
)
from yieldops.cost.attribution import estimate_token_cost
from yieldops.evaluation.anomaly import detect_high_latency
from yieldops.workload.profiling import profile_telemetry


def _record(
    index: int,
    latency: float,
    *,
    model: str = "test-model",
    category: TaskCategory = TaskCategory.CLASSIFICATION,
    tenant: str | None = "tenant-a",
    input_tokens: int | None = 100,
    output_tokens: int | None = 50,
    success: bool = True,
) -> InferenceTelemetry:
    return InferenceTelemetry(
        request_id=uuid4(),
        timestamp_utc=datetime(2025, 1, 1, tzinfo=timezone.utc)
        + timedelta(seconds=index),
        model_name=model,
        tenant_id=tenant,
        task_category=category,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        token_count_provenance=(
            MetricProvenance.MEASURED if input_tokens is not None else None
        ),
        ttft_ms=latency / 2,
        tpot_ms=latency / 2,
        end_to_end_latency_ms=latency,
        output_tokens_per_second=(output_tokens * 1_000 / latency if output_tokens else None),
        success=success,
        provenance=MetricProvenance.MEASURED,
    )


def test_profile_groups_requests_and_preserves_missing_counts() -> None:
    records = [
        _record(0, 10),
        _record(2, 30, category=TaskCategory.SUMMARIZATION, input_tokens=None, output_tokens=None),
    ]

    profile = profile_telemetry(records)

    assert profile.request_count == 2
    assert profile.provenance_counts == {"measured": 2}
    assert profile.requests_without_token_counts == 1
    assert profile.traffic_span_seconds == 2
    assert profile.requests_per_second == 1
    assert profile.peak_requests_per_minute == 2
    assert profile.peak_minute_utc is not None
    assert list(profile.per_minute_request_counts.values()) == [2]
    assert len(profile.by_model) == 1
    assert len(profile.by_task_category) == 2


def test_cost_estimate_uses_explicit_rate_card_and_marks_unpriced_records() -> None:
    records = [
        _record(0, 10),
        _record(1, 10, input_tokens=None, output_tokens=None),
        _record(2, 10, model="unknown-model"),
    ]
    rate_card = CostRateCard(
        rates_by_model={
            "test-model": ModelTokenRates(
                input_usd_per_1k_tokens=1.0, output_usd_per_1k_tokens=2.0
            )
        }
    )

    estimate = estimate_token_cost(records, rate_card)

    assert estimate.total_estimated_cost_usd == 0.2
    assert estimate.priced_request_count == 1
    assert estimate.unpriced_request_count == 2
    assert estimate.mean_estimated_cost_per_priced_request_usd == 0.2
    assert estimate.by_task_category_usd == {"classification": 0.2}
    assert estimate.provenance == MetricProvenance.ESTIMATED


def test_mad_detector_flags_high_latency_using_only_prior_records() -> None:
    records = [_record(index, 50) for index in range(24)]
    records.append(_record(24, 100))

    findings = detect_high_latency(records, window_size=20)

    assert len(findings) == 1
    assert findings[0].observed_latency_ms == 100
    assert findings[0].baseline_median_ms == 50

