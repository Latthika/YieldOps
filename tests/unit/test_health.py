"""Tests for the API health endpoint."""

from fastapi.testclient import TestClient

from yieldops.api.main import app

client = TestClient(app)


def test_health_endpoint_reports_api_is_responsive() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
