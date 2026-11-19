"""Low-cardinality Prometheus text exposition for process-local metrics."""

from collections import defaultdict
from threading import Lock

from yieldops.common.schemas import InferenceTelemetry


class PrometheusMetrics:
    """Track request totals and histogram observations without a runtime package."""

    def __init__(self) -> None:
        self._requests: dict[tuple[str, str], int] = defaultdict(int)
        self._latency_buckets: dict[str, list[int]] = defaultdict(lambda: [0] * 11)
        self._latency_sums: dict[str, float] = defaultdict(float)
        self._latency_counts: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def record(self, telemetry: InferenceTelemetry) -> None:
        provenance = telemetry.provenance.value
        outcome = "success" if telemetry.success else "failure"
        with self._lock:
            self._requests[(provenance, outcome)] += 1
            if telemetry.end_to_end_latency_ms is not None:
                seconds = telemetry.end_to_end_latency_ms / 1_000
                buckets = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
                for index, bound in enumerate(buckets):
                    if seconds <= bound:
                        self._latency_buckets[provenance][index] += 1
                self._latency_sums[provenance] += seconds
                self._latency_counts[provenance] += 1

    def render(self) -> str:
        """Render the Prometheus 0.0.4 text format, including histogram buckets."""
        with self._lock:
            requests = dict(self._requests)
            latency_buckets = {key: tuple(values) for key, values in self._latency_buckets.items()}
            latency_sums = dict(self._latency_sums)
            latency_counts = dict(self._latency_counts)

        lines = [
            "# HELP yieldops_inference_requests_total Inference requests handled by this API process.",
            "# TYPE yieldops_inference_requests_total counter",
        ]
        for (provenance, outcome), count in sorted(requests.items()):
            lines.append(
                f'yieldops_inference_requests_total{{provenance="{provenance}",outcome="{outcome}"}} {count}'
            )

        lines += [
            "# HELP yieldops_inference_latency_seconds Backend-reported end-to-end inference latency in seconds.",
            "# TYPE yieldops_inference_latency_seconds histogram",
        ]
        bucket_bounds = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
        for provenance, counts in sorted(latency_buckets.items()):
            for bound, count in zip(bucket_bounds, counts):
                lines.append(
                    f'yieldops_inference_latency_seconds_bucket{{provenance="{provenance}",le="{bound:g}"}} {count}'
                )
            lines.append(
                f'yieldops_inference_latency_seconds_bucket{{provenance="{provenance}",le="+Inf"}} {latency_counts[provenance]}'
            )
            lines.append(
                f'yieldops_inference_latency_seconds_sum{{provenance="{provenance}"}} {latency_sums[provenance]:g}'
            )
            lines.append(
                f'yieldops_inference_latency_seconds_count{{provenance="{provenance}"}} {latency_counts[provenance]}'
            )
        return "\n".join(lines) + "\n"

