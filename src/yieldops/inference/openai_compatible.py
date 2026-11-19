"""Streaming adapter for OpenAI-compatible local or remote model servers."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from yieldops.common.schemas import (
    InferenceRequest,
    InferenceResponse,
    InferenceTelemetry,
    MetricProvenance,
)


class InferenceBackendError(RuntimeError):
    """Backend failure carrying prompt-free telemetry for the failed request."""

    def __init__(self, telemetry: InferenceTelemetry) -> None:
        super().__init__("inference backend request failed")
        self.telemetry = telemetry


class OpenAICompatibleBackend:
    """Call a streaming `/chat/completions` endpoint such as vLLM or MLX."""

    name = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client = client or httpx.Client(timeout=timeout_seconds)

    @classmethod
    def from_environment(cls) -> OpenAICompatibleBackend:
        base_url = os.environ.get("YIELDOPS_INFERENCE_BASE_URL")
        if not base_url:
            raise ValueError(
                "YIELDOPS_INFERENCE_BASE_URL is required for the openai_compatible backend"
            )
        return cls(
            base_url,
            api_key=os.environ.get("YIELDOPS_INFERENCE_API_KEY"),
            timeout_seconds=float(os.environ.get("YIELDOPS_INFERENCE_TIMEOUT_SECONDS", "120")),
        )

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        request_id = uuid4()
        started = time.perf_counter()
        first_output_at: float | None = None
        chunks: list[str] = []
        usage: dict[str, object] | None = None
        served_model_name = request.model_name
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        payload = {
            "model": request.model_name,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        try:
            with self._client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self._timeout_seconds,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    event = json.loads(data)
                    if isinstance(event.get("model"), str) and event["model"]:
                        served_model_name = event["model"]
                    if isinstance(event.get("usage"), dict):
                        usage = event["usage"]
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    content = (choices[0].get("delta") or {}).get("content")
                    if content:
                        if first_output_at is None:
                            first_output_at = time.perf_counter()
                        chunks.append(str(content))
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1_000
            raise InferenceBackendError(
                self._telemetry(
                    request,
                    request_id,
                    elapsed_ms=elapsed_ms,
                    first_output_ms=None,
                    output_tokens=None,
                    input_tokens=None,
                    token_count_provenance=None,
                    success=False,
                    error_type=type(exc).__name__,
                )
            ) from None

        elapsed_ms = (time.perf_counter() - started) * 1_000
        input_tokens = _usage_int(usage, "prompt_tokens")
        output_tokens = _usage_int(usage, "completion_tokens")
        telemetry_request = request.model_copy(update={"model_name": served_model_name})
        ttft_ms = (first_output_at - started) * 1_000 if first_output_at else None
        tpot_ms = (
            max(elapsed_ms - ttft_ms, 0) / (output_tokens - 1)
            if ttft_ms is not None and output_tokens is not None and output_tokens > 1
            else None
        )
        telemetry = self._telemetry(
            telemetry_request,
            request_id,
            elapsed_ms=elapsed_ms,
            first_output_ms=ttft_ms,
            tpot_ms=tpot_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            token_count_provenance=(
                MetricProvenance.MEASURED
                if input_tokens is not None or output_tokens is not None
                else None
            ),
            success=True,
        )
        return InferenceResponse(
            request_id=request_id,
            model_name=served_model_name,
            output="".join(chunks),
            telemetry=telemetry,
        )

    def _telemetry(
        self,
        request: InferenceRequest,
        request_id,
        *,
        elapsed_ms: float,
        first_output_ms: float | None,
        output_tokens: int | None,
        input_tokens: int | None,
        token_count_provenance: MetricProvenance | None,
        success: bool,
        error_type: str | None = None,
        tpot_ms: float | None = None,
    ) -> InferenceTelemetry:
        return InferenceTelemetry(
            request_id=request_id,
            timestamp_utc=datetime.now(timezone.utc),
            model_name=request.model_name,
            tenant_id=request.tenant_id,
            task_category=request.task_category,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            token_count_provenance=token_count_provenance,
            ttft_ms=first_output_ms,
            tpot_ms=tpot_ms,
            end_to_end_latency_ms=elapsed_ms,
            output_tokens_per_second=(
                output_tokens * 1_000 / elapsed_ms
                if output_tokens is not None and elapsed_ms > 0
                else None
            ),
            success=success,
            provenance=MetricProvenance.MEASURED,
            error_type=error_type,
        )


def _usage_int(usage: dict[str, object] | None, field: str) -> int | None:
    value = usage.get(field) if usage else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None

