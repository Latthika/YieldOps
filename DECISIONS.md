# Architecture Decisions

## ADR-001: Simulation-first local development

**Status:** Accepted for the initial milestone.

**Context:** Initial environment discovery found no available NVIDIA/CUDA benchmark host, and remote GPU access has not been established. Local GPU inference is a separate experiment from NVIDIA/CUDA benchmarking.

**Decision:** Start with deterministic simulated inference telemetry and local service development. Clearly label simulated values. Use a separately approved Linux/NVIDIA environment for CUDA benchmarks when available. Treat vLLM-Metal as an optional, separately labeled local experiment, not as evidence of NVIDIA/CUDA performance.

**Consequences:** Core data contracts, cost logic, API, and orchestration can be developed without cloud spend. GPU-specific metrics and performance claims must wait for compatible hardware. Revisit when remote hardware is confirmed.

## ADR-002: Project Python target

**Status:** Proposed; not installed.

**Decision:** Target Python 3.12 for the first environment. Current vLLM-Metal installation documentation installs Python 3.12. Keep application dependencies minimal and pinned as features are introduced.

**Consequences:** The project uses an isolated Python 3.12 environment. Reassess package compatibility before adding new inference-engine dependencies.
