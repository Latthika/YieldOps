# Initial Metrics

| Metric | Definition in this milestone | Provenance |
|---|---|---|
| Input/output token count | Whitespace-separated pieces in the simulator | Simulated placeholder |
| TTFT | `20 ms + 0.5 ms × input count` | Simulated |
| TPOT | Fixed at 10 ms when output is non-empty | Simulated |
| End-to-end latency | `TTFT + (output count − 1) × TPOT` | Simulated |
| Client HTTP latency | Local `perf_counter` duration around each HTTP request | Measured client-side for that run |
| P50/P95/P99 | Nearest-rank percentile over the current in-memory sample | Inherits the sample provenance |

Percentiles sort the sample and select rank `ceil(p × n)`, using one-based ranks. Empty samples have no percentile. The workload runner's client timings include local HTTP/server overhead and must not be presented as model inference timings.

No GPU utilization, GPU memory, temperature, power, KV-cache, or GPU throughput measurements exist yet. The simulator does not fabricate these values. No cost estimate is produced in this milestone.
