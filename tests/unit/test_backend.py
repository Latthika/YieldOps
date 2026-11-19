"""Tests for the real-backend integration boundary using a mock server."""

import httpx
import pytest

from yieldops.common.schemas import InferenceRequest, MetricProvenance
from yieldops.inference.openai_compatible import (
    InferenceBackendError,
    OpenAICompatibleBackend,
)


def test_streaming_adapter_uses_server_usage_and_measures_timings() -> None:
    body = (
        'data: {"model":"served-model-v2","choices":[{"delta":{"content":"hello "}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"world"}}]}\n\n'
        'data: {"choices":[],"usage":{"prompt_tokens":4,"completion_tokens":2}}\n\n'
        "data: [DONE]\n\n"
    )
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, text=body, headers={"content-type": "text/event-stream"}
            )
        )
    )
    backend = OpenAICompatibleBackend("http://model-server/v1", client=client)

    response = backend.infer(
        InferenceRequest(prompt="synthetic prompt", model_name="test-model")
    )

    assert response.output == "hello world"
    assert response.model_name == "served-model-v2"
    assert response.telemetry.model_name == "served-model-v2"
    assert response.telemetry.provenance == MetricProvenance.MEASURED
    assert response.telemetry.token_count_provenance == MetricProvenance.MEASURED
    assert response.telemetry.input_tokens == 4
    assert response.telemetry.output_tokens == 2
    assert response.telemetry.ttft_ms is not None
    assert response.telemetry.end_to_end_latency_ms is not None
    assert response.telemetry.tpot_ms is not None
    assert "prompt" not in response.telemetry.model_dump()


def test_streaming_adapter_records_failure_without_response_body() -> None:
    def fail(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="private backend error body")

    backend = OpenAICompatibleBackend(
        "http://model-server/v1", client=httpx.Client(transport=httpx.MockTransport(fail))
    )
    with pytest.raises(InferenceBackendError) as raised:
        backend.infer(InferenceRequest(prompt="private prompt"))

    telemetry = raised.value.telemetry
    assert not telemetry.success
    assert telemetry.provenance == MetricProvenance.MEASURED
    assert telemetry.error_type == "HTTPStatusError"
    assert "private" not in str(telemetry.model_dump())

