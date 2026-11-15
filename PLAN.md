# YieldOps 90-Day Plan

Planning assumption: two focused hours per day. This is a milestone plan; daily tasks will be expanded just before each task so commands and acceptance criteria reflect the architecture and environment actually in use.

| Days | Phase | Main outcomes |
|---|---|---|
| 1–10 | Environment and architecture | Discovery, Python environment, repository, contracts, first local service, architecture decisions |
| 11–25 | Inference and telemetry | Backend adapters, workload generator, request metrics, Prometheus/Grafana, tracing |
| 26–40 | Cost and intelligence | Cost attribution, workload profiling, anomaly detection, forecasting baselines |
| 41–55 | Optimization | Configuration experiments, quality/latency constraints, optimization and reproducible benchmarks |
| 56–70 | Agent engineering | LangGraph state, specialized agents/tools, approval flow, evaluation |
| 71–82 | Production engineering | Containers, CI, security/reliability work, Kubernetes only if justified |
| 83–90 | Finalization | End-to-end evidence, benchmark report, docs, reproducible demo and portfolio materials |

## Day 1 — Environment and architecture foundation

- Record the verified host constraints and workspace location.
- Create the initial modular repository and architecture overview.
- Select Python 3.12 as the project interpreter because the current vLLM-Metal installation path specifies Python 3.12. Install only after disk capacity and user approval are established (completed on Day 2).
- Keep inference simulated initially; identify the requirements for a remote GPU benchmark host.
- Done when the repository scaffold and decision record make the local/remote boundary and measurement labeling explicit.

## Day 2 — Python environment and service skeleton (complete)

- Confirmed 56 GiB free disk before setup.
- Installed a uv-managed Python 3.12.16 runtime under the workspace `.tools/` directory and created `.venv/`.
- Added FastAPI, Uvicorn, pytest, HTTPX, and the Starlette-recommended HTTPX2 test-client dependency; `uv.lock` records resolved versions.
- Implemented `GET /health`, returning `{"status":"ok"}`.
- Added a unit test. Result: 1 passed.
- Started Uvicorn on loopback and requested `/health`; result: HTTP 200 with `{"status":"ok"}`. Stopped the server after verification.
- Test versions: FastAPI 0.163.1, Starlette 1.10.0, Uvicorn 0.38.0, pytest 8.4.2, Python 3.12.16.
- Day is done: the isolated environment, endpoint, test, and live response are verified.

## Day 3 — Request and telemetry contracts (complete)

- Added validated inference request, response, telemetry, task category, and provenance models.
- Reject extra request fields and bound prompt and output-token sizes.
- Telemetry summaries exclude prompt and completion text.

## Day 4 — Deterministic simulator (complete)

- Added deterministic simulated output and TTFT/TPOT/end-to-end timing formulas.
- Added `POST /v1/inference`, with telemetry provenance set to simulated.

## Day 5 — Request telemetry aggregation (complete)

- Added a bounded, thread-safe in-memory telemetry store and `GET /v1/telemetry/summary`.
- Added request counts, token totals, and nearest-rank P50/P95/P99 summaries.
- The store resets on process restart; durable storage remains a later task.

## Day 6 — Reproducible synthetic workload (complete)

- Added four general workload categories and a concurrency-limited async HTTP runner.
- The report separates measured local HTTP round trips from simulated server inference timing.

## Day 7 — Integration, verification, and documentation (complete)

- Added integration and unit tests, plus data model and metric assumption documentation.
- Ran 20 requests at concurrency 4: 20 successful responses and 0 errors.
- Full test suite: 10 passed.

## Later daily planning

At the start of each session, expand the next day into objective, tasks, technologies, files, commands, implementation, tests, expected output, learning goals, and definition of done. Do not pre-generate implementation details before prerequisites are verified.
