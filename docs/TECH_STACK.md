# Technology Stack

| Technology | Purpose | Status |
|---|---|---|
| Python 3.12 | Application and experiments | Active; `.python-version` pins 3.12 and the workspace environment reports 3.12.16. |
| FastAPI / Uvicorn | HTTP API and local ASGI server | Active. |
| Pydantic 2 | Validated requests, telemetry, rate cards, and response schemas | Direct runtime dependency. |
| HTTPX | Runtime OpenAI-compatible adapter; async synthetic workload client | Runtime dependency; test/mock transport is used in tests. |
| pytest / HTTPX2 | Unit and TestClient/in-process integration tests | Development dependencies. |
| Python standard library | Async dispatch, threading, timing, percentiles, median/MAD, synthetic data, forecasting, JSON/CSV | Used directly. |
| Prometheus text exposition | `/metrics` counters and histogram | Implemented with a small standard-library exporter; no Prometheus service deployed. |
| MLX / MLX-LM / vLLM-Metal | Possible Apple Silicon real-model runtime | Researched but not installed; waiting for approval to add large packages and download model files. |
| NVIDIA CUDA / vLLM | NVIDIA GPU inference | Not available on this Apple Silicon host; remote GPU host not provisioned. |
| PostgreSQL | Durable telemetry | Evaluated and deferred for this single-process milestone. |
| Grafana / OpenTelemetry | Dashboard and distributed tracing | Not configured. |
| LangGraph / agents | Future orchestration milestone | Not installed or implemented. |
| Docker / Kubernetes | Deployment | Docker unavailable on host; no deployment manifests. |

`pyproject.toml` lists FastAPI, HTTPX, Pydantic, and Uvicorn as runtime dependencies. `uv.lock` pins the resolved tree; pytest and HTTPX2 are development dependencies. No ML, Prometheus, database, or GPU package was added.
