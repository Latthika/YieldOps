"""Summaries over retained request telemetry, grouped by model and workload."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime

from yieldops.common.schemas import (
    InferenceTelemetry,
    WorkloadGroupSummary,
    WorkloadProfile,
)


def profile_telemetry(records: Iterable[InferenceTelemetry]) -> WorkloadProfile:
    """Profile the supplied retained sample without exposing prompts or outputs."""
    sample = tuple(records)
    ordered = sorted(sample, key=lambda record: record.timestamp_utc)
    span = (
        (ordered[-1].timestamp_utc - ordered[0].timestamp_utc).total_seconds()
        if len(ordered) > 1
        else None
    )
    input_tokens = sum(record.input_tokens or 0 for record in sample)
    output_tokens = sum(record.output_tokens or 0 for record in sample)
    minute_counts = _minute_counts(sample)
    peak_minute, peak_count = (
        max(minute_counts.items(), key=lambda item: (item[1], item[0]))
        if minute_counts
        else (None, 0)
    )
    return WorkloadProfile(
        provenance_counts=_counts(record.provenance.value for record in sample),
        request_count=len(sample),
        successful_request_count=sum(record.success for record in sample),
        failed_request_count=sum(not record.success for record in sample),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        requests_without_token_counts=sum(
            record.input_tokens is None or record.output_tokens is None for record in sample
        ),
        traffic_span_seconds=span,
        requests_per_second=(len(sample) / span if span and span > 0 else None),
        output_tokens_per_second=(output_tokens / span if span and span > 0 else None),
        peak_requests_per_minute=peak_count,
        peak_minute_utc=datetime.fromisoformat(peak_minute) if peak_minute else None,
        per_minute_request_counts=minute_counts,
        by_model=_summarize_groups(sample, lambda record: record.model_name),
        by_task_category=_summarize_groups(
            sample, lambda record: record.task_category.value
        ),
    )


def _summarize_groups(records, key_fn) -> list[WorkloadGroupSummary]:
    groups: dict[str, list[InferenceTelemetry]] = defaultdict(list)
    for record in records:
        groups[key_fn(record)].append(record)

    result = []
    for label, group in sorted(groups.items()):
        latencies = sorted(
            record.end_to_end_latency_ms
            for record in group
            if record.end_to_end_latency_ms is not None
        )
        times = sorted(record.timestamp_utc for record in group)
        span = (times[-1] - times[0]).total_seconds() if len(times) > 1 else None
        outputs = sum(record.output_tokens or 0 for record in group)
        result.append(
            WorkloadGroupSummary(
                group=label,
                request_count=len(group),
                successful_request_count=sum(record.success for record in group),
                failed_request_count=sum(not record.success for record in group),
                input_tokens=sum(record.input_tokens or 0 for record in group),
                output_tokens=outputs,
                requests_without_token_counts=sum(
                    record.input_tokens is None or record.output_tokens is None
                    for record in group
                ),
                p50_latency_ms=_nearest_rank(latencies, 0.50),
                p95_latency_ms=_nearest_rank(latencies, 0.95),
                p99_latency_ms=_nearest_rank(latencies, 0.99),
                output_tokens_per_second=(outputs / span if span and span > 0 else None),
            )
        )
    return result


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return dict(sorted(counts.items()))


def _minute_counts(records: tuple[InferenceTelemetry, ...]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        minute = record.timestamp_utc.replace(second=0, microsecond=0).isoformat()
        counts[minute] += 1
    return dict(sorted(counts.items()))


def _nearest_rank(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    rank = max(1, int((len(values) * percentile) + 0.999999999))
    return values[rank - 1]

