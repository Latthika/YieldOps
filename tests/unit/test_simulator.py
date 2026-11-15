"""Tests for deterministic simulated inference metadata."""

from yieldops.common.schemas import InferenceRequest, MetricProvenance
from yieldops.inference.simulator import SimulatedInferenceBackend


def test_simulator_emits_deterministic_synthetic_timings() -> None:
    backend = SimulatedInferenceBackend()
    request = InferenceRequest(prompt="one two three", max_output_tokens=2)

    result = backend.infer(request)

    assert result.output == "simulated completion"
    assert result.telemetry.input_tokens == 3
    assert result.telemetry.output_tokens == 2
    assert result.telemetry.ttft_ms == 21.5
    assert result.telemetry.tpot_ms == 10.0
    assert result.telemetry.end_to_end_latency_ms == 31.5
    assert result.telemetry.provenance == MetricProvenance.SIMULATED
    assert "prompt" not in result.telemetry.model_dump()


def test_simulator_respects_output_token_limit() -> None:
    result = SimulatedInferenceBackend().infer(
        InferenceRequest(prompt="hello", max_output_tokens=1)
    )

    assert result.output == "simulated"
    assert result.telemetry.output_tokens == 1
    assert result.telemetry.end_to_end_latency_ms == result.telemetry.ttft_ms
