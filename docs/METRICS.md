# Metrics and Provenance

| Metric | Source | Provenance / caveat |
|---|---|---|
| Input/output token count | Simulator whitespace pieces, or actual server `usage` fields | `simulated` or `measured`; nullable when a real server omits usage. Whitespace counts are never labeled true tokenizer counts. |
| TTFT | First non-empty streamed content from backend adapter | Simulated for the simulator; measured client-to-first-content wall time for OpenAI-compatible backend. Includes request dispatch/network/queue. |
| TPOT | `(end-to-end - TTFT) / (completion_tokens - 1)` when output count > 1 | Measured only when server returns completion token count; simulator uses its deterministic formula. |
| End-to-end latency | Backend formula or elapsed wall time around streaming request | `simulated` or `measured`; measured adapter time includes transport and queue overhead. |
| Output tokens/second | Output-token count / end-to-end latency | Same provenance limitations as count and latency. |
| Client HTTP latency | `perf_counter` around workload HTTP request | Measured client-side; separate from backend-reported metrics. TestClient benchmark is an in-process path and has no socket. |
| Cost per request / token | Configurable input/output USD per 1,000 tokens | Always `estimated`; based only on user-supplied rate cards and known token usage. |
| Prometheus request count | API process increments for successful and failed backend responses | Process-local; labels include controlled provenance and outcome values. |
| Prometheus latency histogram | Backend timing values | Buckets are separated by provenance; not a measurement of GPU-only execution. |

## Percentiles

Percentiles use nearest rank: sort `n` values and select one-based rank `ceil(p*n)`. Empty samples have no percentile. Summaries apply to the retained in-memory sample, not all historical requests.

## Prometheus endpoint

`GET /metrics` emits Prometheus text exposition with request counters and a cumulative latency histogram (`_bucket`, `_sum`, `_count`). It uses only the standard library and supports local scraping; no Prometheus server, alert rules, Grafana dashboards, or multi-process aggregation are configured. Validate the endpoint against a deployed Prometheus server before treating it as production observability.

## Never infer

No GPU utilization, VRAM, power, temperature, KV-cache, cloud bill, or infrastructure allocation is collected. The simulator's fixed latency formulas are not elapsed inference times. Estimated token charges are not invoices or cost savings.
