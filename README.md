# YieldOps

YieldOps is an AI inference operations platform for measuring workload behavior, attributing infrastructure cost, forecasting capacity, and evaluating evidence-backed serving optimizations. Infrastructure-changing recommendations require human approval.

## Development approach

Begin with reproducible simulated inference telemetry on the local Apple Silicon development machine. Treat simulated values as simulated. Use an authorized Linux/NVIDIA host for CUDA benchmarks when one is available; use local Apple Silicon inference only as a separate, explicitly labeled experiment.

## Project status

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the current milestone and next task. See [PLAN.md](PLAN.md) for the 90-day outline and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the proposed system design.

## Environment

Initial environment discovery found that the local development host is not suitable for NVIDIA/CUDA benchmarking. YieldOps therefore starts with simulated inference and uses a compatible remote Linux/NVIDIA machine for real GPU benchmarks when one is available. The project targets Python 3.12 and uses a locked, isolated environment.

## Principles

- Keep simulated, measured, and estimated values distinct.
- Keep cost and benchmark calculations deterministic and auditable.
- Do not log raw prompts or responses by default.
- Require human approval before infrastructure changes.
- Establish baselines before setting performance claims.

## Run the development API

The project targets Python 3.12 (`.python-version`). The dependency lock is in `uv.lock`. Set up the environment with `uv sync --python 3.12 --group dev`. Start the API from the repository root with `PYTHONPATH=src uv run --frozen uvicorn yieldops.api.main:app --reload`. Run tests with `uv run --frozen pytest`.

The API exposes `GET /health`, `POST /v1/inference`, and `GET /v1/telemetry/summary`. The inference endpoint uses a deterministic simulator and records prompt-free telemetry in memory. In a second terminal, run `PYTHONPATH=src uv run --frozen python scripts/run_synthetic_workload.py --base-url http://127.0.0.1:8000 --requests 20 --concurrency 4`. The runner separates measured local HTTP round-trip time from simulated inference timing. This is a development smoke workload, not a GPU benchmark. See [METRICS.md](docs/METRICS.md) and [EXPERIMENTS.md](docs/EXPERIMENTS.md) for assumptions and the recorded sample run.
