"""Deterministic simulator for API and pipeline development."""

from datetime import datetime, timezone
from uuid import uuid4

from yieldops.common.schemas import (
    InferenceRequest,
    InferenceResponse,
    InferenceTelemetry,
    MetricProvenance,
)


class SimulatedInferenceBackend:
    """Return synthetic outputs and timing values without loading a model."""

    def __init__(
        self,
        *,
        base_ttft_ms: float = 20.0,
        input_token_ttft_ms: float = 0.5,
        tpot_ms: float = 10.0,
        output_text: str = "simulated completion",
    ) -> None:
        self._base_ttft_ms = base_ttft_ms
        self._input_token_ttft_ms = input_token_ttft_ms
        self._tpot_ms = tpot_ms
        self._output_tokens = output_text.split()

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        """Simulate one successful request with explicitly synthetic timings."""
        input_tokens = len(request.prompt.split())
        output_tokens = self._output_tokens[: request.max_output_tokens]
        ttft_ms = self._base_ttft_ms + input_tokens * self._input_token_ttft_ms
        tpot_ms = self._tpot_ms if output_tokens else 0.0
        end_to_end_ms = ttft_ms + max(len(output_tokens) - 1, 0) * tpot_ms
        request_id = uuid4()

        telemetry = InferenceTelemetry(
            request_id=request_id,
            timestamp_utc=datetime.now(timezone.utc),
            model_name=request.model_name,
            tenant_id=request.tenant_id,
            task_category=request.task_category,
            input_tokens=input_tokens,
            output_tokens=len(output_tokens),
            token_count_provenance=MetricProvenance.SIMULATED,
            ttft_ms=ttft_ms,
            tpot_ms=tpot_ms,
            end_to_end_latency_ms=end_to_end_ms,
            output_tokens_per_second=(
                len(output_tokens) * 1_000 / end_to_end_ms if end_to_end_ms else None
            ),
            success=True,
            provenance=MetricProvenance.SIMULATED,
        )
        return InferenceResponse(
            request_id=request_id,
            model_name=request.model_name,
            output=" ".join(output_tokens),
            telemetry=telemetry,
        )
