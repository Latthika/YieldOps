"""Explainable rolling median/MAD high-latency anomaly baseline."""

from collections.abc import Iterable
from statistics import median

from yieldops.common.schemas import AnomalyRecord, InferenceTelemetry


def detect_high_latency(
    records: Iterable[InferenceTelemetry], *, window_size: int = 20, threshold: float = 3.5
) -> list[AnomalyRecord]:
    """Flag high latency using only the preceding rolling window.

    The robust z score is 0.6745 * (observed - median) / MAD. When MAD is zero,
    any higher observation is assigned a large score and is flagged.
    """
    if window_size < 3:
        raise ValueError("window_size must be at least 3")
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    ordered = sorted(records, key=lambda record: record.timestamp_utc)
    history: list[float] = []
    findings = []
    for record in ordered:
        value = record.end_to_end_latency_ms
        if value is None:
            continue
        if len(history) >= window_size:
            baseline = history[-window_size:]
            center = median(baseline)
            mad = median([abs(item - center) for item in baseline])
            score = 0.6745 * (value - center) / mad if mad else (999_999.0 if value > center else 0.0)
            if score >= threshold:
                findings.append(
                    AnomalyRecord(
                        request_id=record.request_id,
                        timestamp_utc=record.timestamp_utc,
                        observed_latency_ms=value,
                        baseline_median_ms=center,
                        robust_z_score=score,
                        provenance=record.provenance,
                    )
                )
        history.append(value)
    return findings
