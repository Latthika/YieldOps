# Technology Stack Audit

| Technology | Purpose / actual use | Location | Status and notes |
|---|---|---|---|
| Python 3.12 | Runtime target | `.python-version`, `pyproject.toml` | Implemented; app uses standard library plus dependencies. |
| FastAPI | HTTP API and request validation integration | `src/yieldops/api/main.py` | Implemented. |
| Pydantic 2 | Request/response/telemetry contracts | `src/yieldops/common/schemas.py` | Used directly but currently only transitive through FastAPI; should eventually be a direct declared dependency. |
| Uvicorn | Local ASGI server | `pyproject.toml`; run command in `README.md` | Implemented for local development; no production deployment configuration. |
| uv | Python environment, dependency resolution, lockfile | `uv.lock`, `pyproject.toml` | Used in development; lockfile present. |
| HTTPX | Async local HTTP workload client | `src/yieldops/workload/generator.py` | Dev dependency. |
| HTTPX2 | Compatibility with current Starlette TestClient path | `pyproject.toml`, `uv.lock` | Dev/test dependency; no application API calls. |
| pytest | Unit and API behavior tests | `tests/` | 10 tests currently pass. |
| Python standard library (`asyncio`, `time`, `threading`, `math`, `datetime`, `uuid`) | Workload concurrency/timing, bounded-store locking/statistics, identifiers | `src/yieldops/` | Used directly; no extra dependency. |
| GitHub | Remote repository/commit hosting | `Latthika/YieldOps` | Development workflow only; not a runtime integration. |
| PostgreSQL | Intended durable storage | `.env.example` has a sample URL only | Not installed/configured/used. No driver or storage code. |
| LangGraph | Intended agent coordination | None | Not installed or used. |
| vLLM / Transformers / PyTorch / MLX | Intended or optional inference paths | None in application dependencies | Not used; no model inference. |
| Prometheus / Grafana / OpenTelemetry / DCGM | Intended observability | Empty `monitoring/` and `dashboards/` placeholders | Not configured; no exporter/dashboard. |
| OpenTelemetry API | Present transitively in the resolved FastAPI dependency graph | `uv.lock` | No app instrumentation, SDK setup, spans, or exporter uses it. |
| scikit-learn / XGBoost / LightGBM | Possible future forecasting | None | Not installed or used. |
| Optuna / OR-Tools | Possible future optimization | None | Not installed or used. |
| Docker / Docker Compose / Kubernetes | Future deployment | Empty placeholders only | Not configured. |

The locked dependency tree currently resolves FastAPI 0.163.1, Pydantic 2.14.3, Starlette 1.10.0, Uvicorn 0.38.0, HTTPX 0.28.1, HTTPX2 2.16.0, and pytest 8.4.2. See `uv.lock` for the complete transitive lock.
