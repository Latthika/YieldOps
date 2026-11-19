# Engineering Gaps and Production Readiness

## What this milestone added

- Backend protocol plus deterministic simulator and optional OpenAI-compatible streaming adapter. Adapter tests use a mock endpoint; real model execution remains unverified.
- Provenance-separated timing and token-count fields, optional true server usage counts, failure telemetry, model/workload labels, and output throughput when derivable.
- A local Prometheus text endpoint, prompt-free profiles, configurable estimated token pricing, rolling MAD anomaly detection, and synthetic forecast baselines.
- Controlled workload patterns and separate client/backend timing. TestClient and MockTransport cover local code paths.

## Remaining gaps

1. **Real model run:** no runtime or model weights installed; no genuine token throughput or quality evidence. MLX/MLX-LM or vLLM-Metal is a plausible Apple Silicon path, but needs user approval for packages and model download.
2. **GPU hardware metrics:** no NVIDIA/CUDA device on this Mac. Apple Metal utilization has not been instrumented. Never publish fake GPU metrics.
3. **Remote benchmark:** no remote GPU server. Uvicorn loopback binding was denied in this sandbox, so the current benchmark is TestClient in-process rather than socket-based.
4. **Persistent telemetry:** memory-only, capped at 10,000 records, reset on restart, and not shared by worker processes. PostgreSQL is deferred pending a demonstrated need.
5. **Observability:** `/metrics` is tested in API tests, but no Prometheus scrape server, Grafana dashboard, alerting, or OpenTelemetry traces have been verified.
6. **Cost:** caller-supplied token rates only. No provider invoice, tenant billing source, actual GPU allocation, idle-cost method, or savings calculation exists.
7. **Forecast and anomaly validity:** only generated data and injected labels; no production baseline, confidence intervals, seasonal drift study, or user workload validation.
8. **Workload API:** synthetic HTTP patterns are mock-tested; live socket concurrency under Uvicorn could not be exercised in the sandbox. The in-process benchmark is not production capacity evidence.
9. **Operations/security:** no auth, rate limiting, quotas, TLS termination, secrets manager, deployment image, CI, rollout, or production runbook. The configured model endpoint should remain local/trusted until security controls exist.
10. **Agents/optimization:** not implemented by design; these belong to later plan milestones.

## Cautions

The model-server adapter forwards prompt content to the configured backend because that is required for inference. Telemetry retains neither prompt nor generated content; error responses are generic and error records retain only exception class. This is a data-minimization property, not an authentication or privacy guarantee.

Do not claim a real model is served, GPU optimized, lower cost, production-ready, or agentic. Safe description: a tested FastAPI inference-monitoring prototype with an optional compatible-backend adapter, deterministic simulation, prompt-free telemetry, and synthetic workload intelligence baselines.
