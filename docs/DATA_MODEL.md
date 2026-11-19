# Data Model

## Inference request

`InferenceRequest` contains prompt content for the backend, model label, optional tenant, task category, output limit, temperature, and top-p. Validation constrains prompt length and generation parameters. The OpenAI-compatible adapter sends those inference fields to the configured server; the simulator ignores sampling controls and remains deterministic.

## Request telemetry

`InferenceTelemetry` includes request UUID and UTC timestamp, model and tenant labels, task category, nullable input/output token counts, token-count provenance, nullable TTFT/TPOT/end-to-end latency, nullable output tokens per second, success, timing provenance, and optional exception class.

Telemetry never includes prompt or completion text. A model server's token `usage` fields are recorded when returned. If usage is absent, token counts stay `null`; the system does not apply whitespace splitting to real inference. The simulator uses whitespace splitting and marks those counts `simulated`.

## Provenance

- `simulated`: produced by deterministic test logic or generated synthetic data.
- `measured`: obtained from wall-clock timing or a model-server tokenizer usage record.
- `estimated`: derived using declared assumptions, currently the caller-supplied token rate card.

Timing provenance and token-count provenance are separate fields because a live backend can provide a measured duration but omit token counts. Summary reports per-provenance counts and known-token totals; missing values are not included in totals.

## Retention and summary

`InMemoryTelemetryStore` retains up to 10,000 latest request records in process memory. It loses records on restart and is not shared across workers. `TelemetrySummary` includes request/success/failure counts, counts by timing provenance, missing-token-count count, known-token totals, and nearest-rank latency percentiles over values with known latency. Its single provenance field is `null` for empty or mixed samples.

## Cost estimate

`CostRateCard` contains per-model input/output USD per 1,000 token rates. `CostEstimate` includes estimated total and per-priced-request mean, priced/unpriced counts, model/task/tenant totals, and the submitted rates. The formula does not include GPU time, idle capacity, or provider invoice amounts.

## Workload profile

`WorkloadProfile` groups records by model and task category. It also reports UTC minute-bucket request counts and the busiest minute, alongside total sample span and throughput. Buckets describe the retained sample only; they are not a durable traffic history.
