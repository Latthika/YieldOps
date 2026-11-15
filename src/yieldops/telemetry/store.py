"""Small in-memory telemetry store for the initial development service."""

from math import ceil
from threading import Lock

from yieldops.common.schemas import (
    InferenceTelemetry,
    MetricProvenance,
    TelemetrySummary,
)


class InMemoryTelemetryStore:
    """Keep request metadata in process memory; restart clears this store."""

    def __init__(self, max_records: int = 10_000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be positive")
        self._max_records = max_records
        self._records: list[InferenceTelemetry] = []
        self._lock = Lock()

    def add(self, record: InferenceTelemetry) -> None:
        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_records:
                del self._records[: len(self._records) - self._max_records]

    def summary(self) -> TelemetrySummary:
        with self._lock:
            records = tuple(self._records)

        latencies = sorted(record.end_to_end_latency_ms for record in records)
        return TelemetrySummary(
            request_count=len(records),
            simulated_request_count=sum(
                record.provenance == MetricProvenance.SIMULATED for record in records
            ),
            total_input_tokens=sum(record.input_tokens for record in records),
            total_output_tokens=sum(record.output_tokens for record in records),
            p50_end_to_end_latency_ms=_nearest_rank(latencies, 0.50),
            p95_end_to_end_latency_ms=_nearest_rank(latencies, 0.95),
            p99_end_to_end_latency_ms=_nearest_rank(latencies, 0.99),
            provenance=MetricProvenance.SIMULATED,
        )


def _nearest_rank(values: list[float], percentile: float) -> float | None:
    """Return the nearest-rank percentile; an empty sample has no percentile."""
    if not values:
        return None
    rank = max(1, ceil(len(values) * percentile))
    return values[rank - 1]
