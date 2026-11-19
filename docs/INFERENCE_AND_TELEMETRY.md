# Inference and Telemetry

## Backend implementations

`InferenceBackend` in `src/yieldops/inference/backend.py` defines the synchronous `infer(request)` boundary. The API dispatches the call via `asyncio.to_thread` to keep blocking work off the ASGI event loop.

- `SimulatedInferenceBackend` remains the default. It returns fixed text, whitespace-based counts, and formula-derived timings. Every one of those fields is labeled `simulated`.
- `OpenAICompatibleBackend` sends a streaming chat-completion request to `<base_url>/chat/completions`. It supports the requested model label, max output tokens, temperature, and top-p. It measures elapsed time and first content arrival with `perf_counter`; it records input/output counts only if the server returns usage data. It retains no prompt or response text in telemetry. Backend failures produce a failure record with only the exception class, then the API returns a generic 502 message.

Configuration is through process environment variables; `.env.example` is a template and is not automatically loaded:

```bash
export YIELDOPS_INFERENCE_BACKEND=openai_compatible
export YIELDOPS_INFERENCE_BASE_URL=http://127.0.0.1:8001/v1
export YIELDOPS_INFERENCE_API_KEY=   # only for a server that requires one
export YIELDOPS_INFERENCE_TIMEOUT_SECONDS=120
PYTHONPATH=src ./.venv/bin/uvicorn yieldops.api.main:app --host 127.0.0.1 --port 8000
```

The API key should be provided through a local shell secret mechanism, never committed. The adapter expects an OpenAI-compatible streaming endpoint; server-specific support for `stream_options.include_usage` must be verified. Tests use an in-process mock transport and do not demonstrate model execution.

## API routes

- `GET /health`: confirms the API process responds.
- `POST /v1/inference`: runs the configured adapter and records request metadata.
- `GET /v1/telemetry/summary`: summarizes the latest retained in-memory records.
- `GET /v1/telemetry/profile`: groups retained telemetry by model/task category and reports minute-level traffic peaks.
- `GET /v1/telemetry/anomalies`: evaluates high-latency values with a rolling median/MAD baseline.
- `POST /v1/telemetry/cost-estimate`: applies a caller-supplied per-model token rate card.
- `GET /metrics`: exposes process-local Prometheus counters and a latency histogram in text format.

## Metric meaning and provenance

- `provenance` applies to timing values: simulator formulas are `simulated`; backend wall-clock durations are `measured`; derived prices are `estimated`.
- `token_count_provenance` is separate. The simulator's whitespace pieces are `simulated`; counts returned by the model server are `measured`; if server usage is absent, both count fields are `null`.
- `ttft_ms` is the adapter's elapsed time until the first non-empty streaming content. It includes request dispatch and network/queue delay to the server, not only GPU kernel time.
- `end_to_end_latency_ms` is measured from before the HTTP request to the end of the stream. It includes server, transport, and response streaming time.
- `tpot_ms` is derived from measured end-to-end and TTFT divided by `completion_tokens - 1`; it is reported only when server usage provides more than one completion token.
- `output_tokens_per_second` is server-reported output count divided by measured or simulated end-to-end time. It is null when the count is unavailable.
- Client HTTP round-trip time in the workload runner is separate from backend timing.

Telemetry fields exclude prompt and completion contents. The in-memory store retains up to 10,000 recent records, loses them at restart, and is not shared between workers. The cost estimator does not use inference latency to infer GPU cost.

## Tested boundaries and remaining work

The OpenAI-compatible request/stream parser is tested with an HTTPX mock server, including token usage and failure handling. No real model endpoint, tokenizer, GPU, Prometheus server, Grafana dashboard, or OpenTelemetry exporter has been configured. A local TestClient benchmark measures ASGI application overhead only; no socket-based workload ran because the sandbox denied binding a local server port.

OpenTelemetry tracing was evaluated and deferred: the current request path is a single API process with no queue or downstream service graph, and there is no collector endpoint to receive exported spans. Add trace context propagation and exporter configuration when real model-service calls are deployed and can be observed end to end.
