"""Tests for bounded in-memory telemetry aggregation."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from yieldops.common.schemas import InferenceTelemetry, MetricProvenance, TaskCategory
from yieldops.telemetry.store import InMemoryTelemetryStore


def _record(latency_ms: float, input_tokens: int = 2) -> InferenceTelemetry:
    return InferenceTelemetry(
        request_id=uuid4(),
        timestamp_utc=datetime.now(timezone.utc),
        model_name="test-model",
        tenant_id=None,
        task_category=TaskCategory.OTHER,
        input_tokens=input_tokens,
        output_tokens=2,
        ttft_ms=latency_ms - 10,
        tpot_ms=10,
        end_to_end_latency_ms=latency_ms,
        success=True,
        provenance=MetricProvenance.SIMULATED,
    )


def test_summary_uses_nearest_rank_percentiles_and_token_totals() -> None:
    store = InMemoryTelemetryStore()
    for latency in (31.0, 32.0, 33.0):
        store.add(_record(latency))

    result = store.summary()

    assert result.request_count == 3
    assert result.simulated_request_count == 3
    assert result.total_input_tokens == 6
    assert result.total_output_tokens == 6
    assert result.p50_end_to_end_latency_ms == 32.0
    assert result.p95_end_to_end_latency_ms == 33.0
    assert result.p99_end_to_end_latency_ms == 33.0
    assert result.provenance == MetricProvenance.SIMULATED


def test_summary_is_empty_before_any_requests() -> None:
    result = InMemoryTelemetryStore().summary()

    assert result.request_count == 0
    assert result.p50_end_to_end_latency_ms is None
    assert result.p95_end_to_end_latency_ms is None
    assert result.p99_end_to_end_latency_ms is None


def test_store_rejects_invalid_capacity_and_keeps_only_recent_records() -> None:
    with pytest.raises(ValueError, match="max_records must be positive"):
        InMemoryTelemetryStore(max_records=0)

    store = InMemoryTelemetryStore(max_records=2)
    store.add(_record(10.0))
    store.add(_record(20.0))
    store.add(_record(30.0))

    summary = store.summary()
    assert summary.request_count == 2
    assert summary.p50_end_to_end_latency_ms == 20.0
    assert summary.p95_end_to_end_latency_ms == 30.0
