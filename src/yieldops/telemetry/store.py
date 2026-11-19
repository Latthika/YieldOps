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

    def snapshot(self) -> tuple[InferenceTelemetry, ...]:
        """Return a stable copy for profiling and cost analysis."""
        with self._lock:
            return tuple(self._records)

    def summary(self) -> TelemetrySummary:
        with self._lock:
            records = tuple(self._records)

        latencies = sorted(
            record.end_to_end_latency_ms
            for record in records
            if record.end_to_end_latency_ms is not None
        )
        provenances = {record.provenance for record in records}
        return TelemetrySummary(
            request_count=len(records),
            successful_request_count=sum(record.success for record in records),
            failed_request_count=sum(not record.success for record in records),
            simulated_request_count=sum(
                record.provenance == MetricProvenance.SIMULATED for record in records
            ),
            measured_request_count=sum(
                record.provenance == MetricProvenance.MEASURED for record in records
            ),
            estimated_request_count=sum(
                record.provenance == MetricProvenance.ESTIMATED for record in records
            ),
            requests_without_token_counts=sum(
                record.input_tokens is None or record.output_tokens is None
                for record in records
            ),
            total_input_tokens=sum(record.input_tokens or 0 for record in records),
            total_output_tokens=sum(record.output_tokens or 0 for record in records),
            p50_end_to_end_latency_ms=_nearest_rank(latencies, 0.50),
            p95_end_to_end_latency_ms=_nearest_rank(latencies, 0.95),
            p99_end_to_end_latency_ms=_nearest_rank(latencies, 0.99),
            provenance=next(iter(provenances)) if len(provenances) == 1 else None,
        )


def _nearest_rank(values: list[float], percentile: float) -> float | None:
    """Return the nearest-rank percentile; an empty sample has no percentile."""
    if not values:
        return None
    rank = max(1, ceil(len(values) * percentile))
    return values[rank - 1]
