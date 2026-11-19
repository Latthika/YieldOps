"""Integration coverage for inference telemetry flow through the API."""

from fastapi.testclient import TestClient
from datetime import datetime, timezone
from uuid import uuid4

from yieldops.api import main
from yieldops.common.schemas import InferenceTelemetry, MetricProvenance, TaskCategory
from yieldops.inference.openai_compatible import InferenceBackendError
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
    assert summary["successful_request_count"] == 1
    assert summary["failed_request_count"] == 0
    assert summary["p50_end_to_end_latency_ms"] == 32.0
    assert summary["p95_end_to_end_latency_ms"] == 32.0
    assert summary["p99_end_to_end_latency_ms"] == 32.0


def test_inference_request_validation_rejects_empty_prompt() -> None:
    client = TestClient(main.app)

    response = client.post("/v1/inference", json={"prompt": ""})

    assert response.status_code == 422


def test_telemetry_profile_cost_estimate_and_prometheus_export(monkeypatch) -> None:
    monkeypatch.setattr(main, "telemetry_store", InMemoryTelemetryStore())
    client = TestClient(main.app)
    inference = client.post(
        "/v1/inference",
        json={
            "prompt": "synthetic sample",
            "model_name": "demo-model",
            "task_category": "classification",
            "max_output_tokens": 2,
        },
    )
    assert inference.status_code == 200

    profile = client.get("/v1/telemetry/profile")
    assert profile.status_code == 200
    assert profile.json()["request_count"] == 1
    assert profile.json()["by_model"][0]["group"] == "demo-model"

    estimate = client.post(
        "/v1/telemetry/cost-estimate",
        json={
            "rates_by_model": {
                "demo-model": {
                    "input_usd_per_1k_tokens": 1.0,
                    "output_usd_per_1k_tokens": 2.0,
                }
            }
        },
    )
    assert estimate.status_code == 200
    assert estimate.json()["provenance"] == "estimated"
    assert estimate.json()["priced_request_count"] == 1

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "yieldops_inference_requests_total" in metrics.text
    assert "# TYPE yieldops_inference_latency_seconds histogram" in metrics.text
    assert 'yieldops_inference_latency_seconds_bucket{provenance="simulated",le="+Inf"}' in metrics.text
    assert "yieldops_inference_latency_seconds_count" in metrics.text


def test_backend_failure_is_recorded_and_api_error_is_generic(monkeypatch) -> None:
    monkeypatch.setattr(main, "telemetry_store", InMemoryTelemetryStore())
    telemetry = InferenceTelemetry(
        request_id=uuid4(),
        timestamp_utc=datetime.now(timezone.utc),
        model_name="demo-model",
        tenant_id=None,
        task_category=TaskCategory.OTHER,
        input_tokens=None,
        output_tokens=None,
        token_count_provenance=None,
        ttft_ms=None,
        tpot_ms=None,
        end_to_end_latency_ms=12.0,
        output_tokens_per_second=None,
        success=False,
        provenance=MetricProvenance.MEASURED,
        error_type="ConnectError",
    )

    class FailingBackend:
        name = "test"

        def infer(self, _request):
            raise InferenceBackendError(telemetry)

    monkeypatch.setattr(main, "inference_backend", FailingBackend())
    response = TestClient(main.app).post("/v1/inference", json={"prompt": "private"})

    assert response.status_code == 502
    assert response.json() == {"detail": "inference backend request failed"}
    summary = TestClient(main.app).get("/v1/telemetry/summary").json()
    assert summary["failed_request_count"] == 1
    assert summary["measured_request_count"] == 1
    assert summary["requests_without_token_counts"] == 1
