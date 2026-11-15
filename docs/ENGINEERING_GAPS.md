# Engineering Gaps and Production Readiness

## Highest-priority gaps

1. **No real inference backend:** current output and latency are deterministic simulation. No NVIDIA/CUDA benchmark is possible from this implementation.
2. **No durable storage:** telemetry is process-local, capped at 10,000 records, lost on restart, and not shared across workers.
3. **No actual observability stack:** no Prometheus scrape endpoint/exporter, Grafana dashboard, OpenTelemetry traces, or GPU/DCGM metrics.
4. **No cost attribution:** no pricing source, allocation policy, measurement period, provider bill integration, or cost calculation.
5. **No optimization/evaluation:** no model quality evaluation, baseline comparison, optimizer, or evidence-backed recommendations.
6. **No agents:** LangGraph and approval workflow are not implemented; policy text in README is not an enforcement mechanism.
7. **No deployment/CI:** no Dockerfile, Compose config, Kubernetes manifests, GitHub Actions workflow, or deployment/runbook validation.

## Code-level concerns

- `health_check` is static and does not check dependencies or readiness.
- `run_inference` is declared async but directly calls a synchronous backend. That is trivial today; a blocking model call would block the event loop unless moved to an appropriate worker/thread/async adapter.
- Simulator values are constructor defaults in code, not validated configuration. Negative values could fail Pydantic metric validation at runtime.
- Token fields are named tokens but are whitespace counts, not model tokenizer counts.
- `TelemetrySummary.provenance` is hard-coded simulated and the store is not designed to correctly summarize mixed provenance. This is acceptable only for the single simulator path.
- Failed HTTP/API requests are not recorded as request telemetry. The workload runner counts errors in its own output only.
- The in-memory summary is a bounded recent sample; `request_count` is not an all-time count. The API does not expose the retained window size or uptime.
- `model_name` and `tenant_id` are caller-provided labels without a model registry or tenant authorization.
- `pydantic` is imported directly but not declared as a direct dependency in `pyproject.toml` (it currently arrives through FastAPI).
- TestClient integration tests run in-process. There are no tests for concurrency, process restart, persistence, performance/evaluation, or live model behavior.
- No coverage percentage, linter, type checker, or security scanner is configured.
- `.env.example` documents environment names, but the application does not load or use these variables.

## Security and operational gaps

The app has no authentication, rate limiting, request quotas, TLS termination, structured logging policy, secrets management, tenant isolation, or production error policy. It does not persist prompt text, but requests necessarily pass through process memory. The current dev service should not be exposed publicly or used for live workloads.

## Do not claim yet

Do not call the current service an LLM platform, agentic system, GPU monitor, cost optimizer, forecaster, benchmark suite, or production-ready deployment. Accurate description: a tested FastAPI simulator and telemetry contract prototype with a synthetic HTTP smoke runner.
