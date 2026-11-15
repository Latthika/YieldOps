"""Reproducible synthetic HTTP workload runner."""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Iterable

import httpx

PROMPTS = (
    ("structured_extraction", "Extract the product and quantity from this synthetic order."),
    ("classification", "Classify this synthetic support message by topic."),
    ("summarization", "Summarize this short synthetic project update."),
    ("question_answering", "Answer a question about this synthetic example."),
)


def nearest_rank(values: Iterable[float], percentile: float) -> float | None:
    """Calculate nearest-rank percentile for a non-empty sample."""
    ordered = sorted(values)
    if not ordered:
        return None
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be greater than 0 and at most 1")
    return ordered[max(1, math.ceil(len(ordered) * percentile)) - 1]


async def run_workload(base_url: str, request_count: int, concurrency: int) -> dict[str, object]:
    """Run synthetic requests and separate measured client from simulated server times."""
    if request_count < 1 or concurrency < 1:
        raise ValueError("request_count and concurrency must both be positive")

    semaphore = asyncio.Semaphore(concurrency)
    client_latencies: list[float] = []
    errors = 0

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        async def send_one(index: int) -> None:
            nonlocal errors
            category, prompt = PROMPTS[index % len(PROMPTS)]
            payload = {
                "prompt": f"Synthetic request {index}: {prompt}",
                "model_name": "yieldops-simulator",
                "task_category": category,
                "max_output_tokens": 16,
            }
            async with semaphore:
                started = time.perf_counter()
                try:
                    response = await client.post("/v1/inference", json=payload)
                    client_latencies.append((time.perf_counter() - started) * 1_000)
                    if response.status_code != 200:
                        errors += 1
                except httpx.HTTPError:
                    errors += 1

        await asyncio.gather(*(send_one(index) for index in range(request_count)))
        summary_response = await client.get("/v1/telemetry/summary")
        summary_response.raise_for_status()
        summary = summary_response.json()

    return {
        "requested": request_count,
        "successful_http_requests": request_count - errors,
        "errors": errors,
        "client_http_latency_ms": {
            "provenance": "measured",
            "p50": nearest_rank(client_latencies, 0.50),
            "p95": nearest_rank(client_latencies, 0.95),
            "p99": nearest_rank(client_latencies, 0.99),
        },
        "server_inference_latency_ms": {
            "provenance": summary["provenance"],
            "request_count_in_process": summary["request_count"],
            "p50": summary["p50_end_to_end_latency_ms"],
            "p95": summary["p95_end_to_end_latency_ms"],
            "p99": summary["p99_end_to_end_latency_ms"],
        },
    }
