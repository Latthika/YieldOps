# Optimization and Evaluation: Current State

## Implemented

Only request simulation, telemetry aggregation, and a small synthetic HTTP smoke runner are implemented. The runner sends four fixed task-category prompt patterns with configurable request count and concurrency. It reports client-side HTTP percentiles separately from simulator-generated server percentiles.

## Not implemented

- No optimization algorithm, search space, candidate configuration, model routing, quantization, batching, caching, or resource allocation planner.
- No cost model or savings calculation.
- No output-quality metric or dataset.
- No model baseline-versus-optimized experiment.
- No Optuna, OR-Tools, benchmark harness, Locust, or performance/evaluation test.
- No recommendations are produced.

## Experiment actually executed

`docs/EXPERIMENTS.md` records one run of 20 requests at concurrency 4. It had 20 successful HTTP responses and 0 errors. Client HTTP p50/p95/p99 were 1.87/5.14/16.14 ms for that local run. Simulator timings were p50/p95/p99 35/36/36 ms from fixed formulas. There were no repeated trials, real model calls, GPU metrics, quality measurements, or cost data.

This is integration evidence only. It does not show that YieldOps improves inference efficiency. Percentile computation is telemetry aggregation, not optimization.

## Evidence required before claiming improvement

Use the same evaluation prompts and workload mix for baseline and candidate configurations; record exact model/runtime/hardware/software, repetitions, warm-up, concurrency, input/output token distributions, failures, quality scores, latency, throughput, memory/utilization, and price/allocation assumptions. Enforce quality and latency constraints before comparing cost per successful task. Report variance and negative outcomes as well as gains.
