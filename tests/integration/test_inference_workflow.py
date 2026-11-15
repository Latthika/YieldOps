"""Integration coverage for inference telemetry flow through the API."""

from fastapi.testclient import TestClient

from yieldops.api import main
from yieldops.telemetry.store import InMemoryTelemetryStore


def test_inference_request_flows_into_prompt_free_summary(monkeypatch) -> None:
    monkeypatch.setattr(main, "telemetry_store", InMemoryTelemetryStore())
    client = TestClient(main.app)

    response = client.post(
        "/v1/inference",
        json={
            "prompt": "classify this synthetic example",
            "model_name": "demo-model",
            "tenant_id": "demo-tenant",
            "task_category": "classification",
            "max_output_tokens": 8,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["output"] == "simulated completion"
    assert payload["telemetry"]["input_tokens"] == 4
    assert payload["telemetry"]["provenance"] == "simulated"
    assert "prompt" not in payload

    summary = client.get("/v1/telemetry/summary").json()
    assert summary["request_count"] == 1
    assert summary["simulated_request_count"] == 1
    assert summary["p50_end_to_end_latency_ms"] == 32.0
    assert summary["p95_end_to_end_latency_ms"] == 32.0
    assert summary["p99_end_to_end_latency_ms"] == 32.0


def test_inference_request_validation_rejects_empty_prompt() -> None:
    client = TestClient(main.app)

    response = client.post("/v1/inference", json={"prompt": ""})

    assert response.status_code == 422
