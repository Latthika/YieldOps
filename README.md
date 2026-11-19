# YieldOps

YieldOps is an early-stage inference operations prototype for studying backend boundaries, request telemetry, workload profiling, transparent token-cost estimates, and simple forecasting/anomaly baselines.

## Current implementation

- FastAPI request API with a deterministic simulator as the default backend.
- Typed inference backend interface and optional OpenAI-compatible streaming adapter. The adapter is mock-tested; no live model server or model weights are included.
- Prompt-free request telemetry with separate timing and token-count provenance.
- In-memory summary, per-minute/model/workload profile, anomaly, and user-rate-card cost-estimate endpoints.
- Standard-library Prometheus text endpoint at `/metrics`.
- Synthetic workload runner and reproducible synthetic forecasting/anomaly experiments.
- 20 automated unit and integration tests covering the simulator, adapter boundary, telemetry, and analysis code.

This is not yet an LLM platform or production monitoring service. No real model inference, GPU metrics, database, Grafana dashboard, OpenTelemetry tracing, actual cloud costs, agents, optimizer, or deployment stack is configured. The test and experiment evidence is explicitly labeled in [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md).

## Run locally

The project targets Python 3.12. Start with the isolated workspace environment:

```bash
uv sync --python 3.12 --group dev
PYTHONPATH=src uv run --frozen uvicorn yieldops.api.main:app --reload
```

Try simulated inference and the telemetry endpoints at `http://127.0.0.1:8000/docs`. Metrics are exposed at `/metrics`.

Run the synthetic HTTP workload in another terminal:

```bash
PYTHONPATH=src uv run --frozen python scripts/run_synthetic_workload.py \
  --base-url http://127.0.0.1:8000 --requests 100 --concurrency 4 \
  --pattern mixed --seed 42
```

Patterns are `mixed`, `classification`, and `bursty`. Client HTTP round-trip measurements and backend telemetry are reported separately.

Run tests and offline synthetic experiments:

```bash
./.venv/bin/python -m pytest -q
PYTHONPATH=src ./.venv/bin/python scripts/run_inprocess_benchmark.py --requests 100 --repetitions 3
PYTHONPATH=src ./.venv/bin/python scripts/run_milestone_experiments.py
```

## Optional compatible model server

A server must implement the OpenAI-compatible streaming chat completion endpoint expected by this adapter. Configure the API in its environment, then start it. Never commit an API key.

```bash
export YIELDOPS_INFERENCE_BACKEND=openai_compatible
export YIELDOPS_INFERENCE_BASE_URL=http://127.0.0.1:8001/v1
export YIELDOPS_INFERENCE_API_KEY=   # only if required
PYTHONPATH=src uv run --frozen uvicorn yieldops.api.main:app --reload
```

The Apple M4 host may support a small MLX-backed experiment, but no large inference package or model was installed or downloaded. See [`docs/MODELS_AND_ML.md`](docs/MODELS_AND_ML.md) before setting up a runtime.

## Learn the implementation

- [Architecture](docs/ARCHITECTURE.md)
- [Inference and telemetry](docs/INFERENCE_AND_TELEMETRY.md)
- [Data provenance](docs/DATASETS_AND_DATA_PROVENANCE.md)
- [Experiment results](docs/EXPERIMENTS.md)
- [Cost and workload evaluation](docs/OPTIMIZATION_AND_EVALUATION.md)

Internal learning materials are maintained separately and are not part of the public repository.
