"""Reproducible synthetic HTTP workload runner."""

from __future__ import annotations

import asyncio
import math
import random
import time
from collections import Counter
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


async def run_workload(
    base_url: str,
    request_count: int,
    concurrency: int,
    *,
    pattern: str = "mixed",
    seed: int = 42,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, object]:
    """Run controlled synthetic traffic and separate client from backend timing."""
    if request_count < 1 or concurrency < 1:
        raise ValueError("request_count and concurrency must both be positive")
    if pattern not in {"mixed", "classification", "bursty"}:
        raise ValueError("pattern must be mixed, classification, or bursty")

    semaphore = asyncio.Semaphore(concurrency)
    rng = random.Random(seed)
    client_latencies: list[float] = []
    server_latencies: list[float] = []
    server_telemetry: list[dict[str, object]] = []
    task_categories: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    transport_errors = 0
    started_run = time.perf_counter()

    async with httpx.AsyncClient(
        base_url=base_url, timeout=30.0, transport=transport
    ) as client:
        async def send_one(index: int) -> None:
            nonlocal transport_errors
            if pattern == "classification":
                category, prompt = PROMPTS[1]
            elif pattern == "mixed":
                category, prompt = rng.choice(PROMPTS)
            else:
                category, prompt = PROMPTS[index % len(PROMPTS)]
                await asyncio.sleep((index // concurrency) * 0.25)
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
                    status_counts[str(response.status_code)] += 1
                    if response.status_code == 200:
                        telemetry = response.json().get("telemetry", {})
                        if isinstance(telemetry, dict):
                            server_telemetry.append(telemetry)
                            task_categories[str(telemetry.get("task_category", "unknown"))] += 1
                        latency = telemetry.get("end_to_end_latency_ms")
                        latency = telemetry.get("end_to_end_latency_ms")
                        if isinstance(latency, (int, float)):
                            server_latencies.append(float(latency))
                except httpx.HTTPError:
                    transport_errors += 1

        await asyncio.gather(*(send_one(index) for index in range(request_count)))
        summary_response = await client.get("/v1/telemetry/summary")
        summary_response.raise_for_status()
        summary = summary_response.json()

    elapsed_seconds = time.perf_counter() - started_run
    success_count = status_counts.get("200", 0)

    return {
        "requested": request_count,
        "pattern": pattern,
        "seed": seed,
        "concurrency_limit": concurrency,
        "elapsed_seconds": elapsed_seconds,
        "successful_http_requests": success_count,
        "success_rate": success_count / request_count,
        "task_category_counts": dict(sorted(task_categories.items())),
        "http_status_counts": dict(sorted(status_counts.items())),
        "transport_errors": transport_errors,
        "requests_per_second": success_count / elapsed_seconds if elapsed_seconds else None,
        "client_http_latency_ms": {
            "provenance": "measured",
            "p50": nearest_rank(client_latencies, 0.50),
            "p95": nearest_rank(client_latencies, 0.95),
            "p99": nearest_rank(client_latencies, 0.99),
        },
        "server_inference_latency_ms": {
            "provenance_counts": dict(
                Counter(item.get("provenance", "unknown") for item in server_telemetry)
            ),
            "request_count_in_this_run": len(server_latencies),
            "p50": nearest_rank(server_latencies, 0.50),
            "p95": nearest_rank(server_latencies, 0.95),
            "p99": nearest_rank(server_latencies, 0.99),
        },
        "process_sample_summary": summary,
    }
