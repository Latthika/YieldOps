# Inference and Telemetry: Current State

## Inference engine

The only backend is `SimulatedInferenceBackend` in `src/yieldops/inference/simulator.py`. It executes local Python string/count/formula operations and returns fixed synthetic output. It is not vLLM, Hugging Face Transformers, PyTorch inference, MLX, or an external model API. No model is served.

## API

- `GET /health`: static `{ "status": "ok" }`; process responsiveness only.
- `POST /v1/inference`: validates `InferenceRequest`, simulates a response, stores metadata, returns output and telemetry.
- `GET /v1/telemetry/summary`: returns retained count/token totals and latency percentiles.

Routes are in `src/yieldops/api/main.py`. Pydantic contracts are in `src/yieldops/common/schemas.py`.

## Metrics and provenance

The simulator emits synthetic token counts, TTFT, TPOT, and end-to-end latency. It does not sleep for those durations and does not measure elapsed inference time. Counts use whitespace splitting rather than a model tokenizer. The local workload client separately times each HTTP request with `time.perf_counter`; those values include client/server/application overhead and belong only to the recorded run.

`InMemoryTelemetryStore` keeps at most 10,000 recent telemetry objects and calculates nearest-rank P50/P95/P99 over the stored simulated latencies. Restarting the service erases the sample. The summary's `provenance` is currently hard-coded to `simulated`, consistent with its only caller/backend today.

Not collected: GPU utilization, VRAM, temperature, power, KV-cache use, queue depth, true tokenization, true TTFT/TPOT, model throughput, failed inference records, traces, or durable logs. No Prometheus exporter, Grafana dashboard, OpenTelemetry SDK instrumentation/exporter, or DCGM Exporter is configured.

## Cost

No inference cost is calculated. The `YIELDOPS_DATABASE_URL` example is not loaded by the application, and there is no database client, pricing configuration, GPU allocation method, cloud billing source, or cost-per-request formula. Do not treat HTTP latency or simulated server timing as GPU billing time.
