"""Backend contract shared by simulated and real inference adapters."""

from typing import Protocol

from yieldops.common.schemas import InferenceRequest, InferenceResponse


class InferenceBackend(Protocol):
    """Synchronous backend boundary; the API runs it outside the event loop."""

    name: str

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        """Return output plus prompt-free request telemetry."""

