"""Tests for synthetic workload helpers."""

import asyncio

import httpx
import pytest

from yieldops.workload.generator import nearest_rank, run_workload


def test_nearest_rank_percentiles() -> None:
    assert nearest_rank([4.0, 1.0, 3.0, 2.0], 0.50) == 2.0
    assert nearest_rank([4.0, 1.0, 3.0, 2.0], 0.95) == 4.0


def test_nearest_rank_handles_empty_samples_and_invalid_percentiles() -> None:
    assert nearest_rank([], 0.95) is None
    with pytest.raises(ValueError, match="percentile"):
        nearest_rank([1.0], 0)


def test_workload_runner_reports_client_and_backend_measurements_separately() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/telemetry/summary":
            return httpx.Response(200, json={"request_count": 3, "provenance": "simulated"})
        return httpx.Response(
            200,
            json={
                "telemetry": {
                    "end_to_end_latency_ms": 35.0,
                    "provenance": "simulated",
                    "task_category": "classification",
                }
            },
        )

    report = asyncio.run(
        run_workload(
            "http://test",
            request_count=3,
            concurrency=2,
            pattern="classification",
            seed=3,
            transport=httpx.MockTransport(handler),
        )
    )

    assert report["successful_http_requests"] == 3
    assert report["success_rate"] == 1
    assert report["task_category_counts"] == {"classification": 3}
    assert report["client_http_latency_ms"]["provenance"] == "measured"
    assert report["server_inference_latency_ms"]["provenance_counts"] == {"simulated": 3}
    assert report["server_inference_latency_ms"]["p50"] == 35
