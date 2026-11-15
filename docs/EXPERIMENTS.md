# Experiment Log

## EXP-000: Week-one simulated pipeline smoke run

- **Date:** 2026-11-15 (local development session)
- **Backend:** Deterministic YieldOps simulator; no model weights or GPU used.
- **Workload:** 20 synthetic requests, concurrency 4, four general workload categories.
- **HTTP outcome:** 20 successful responses, 0 errors.
- **Measured local client HTTP latency:** P50 1.87 ms, P95 5.14 ms, P99 16.14 ms for this run.
- **Simulated inference latency:** P50 35 ms, P95 36 ms, P99 36 ms from the fixed formula in `METRICS.md`.
- **Interpretation:** This verifies API/workload integration and provenance labeling. The sample is small, in-process, and uses simulated inference. Client values include local HTTP and application overhead. This is not an inference benchmark and supports no GPU performance or optimization claim.
