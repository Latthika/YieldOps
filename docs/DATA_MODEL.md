# Initial Data Model

## Inference request

The API accepts a prompt, model name, optional tenant identifier, workload category, and maximum output-token limit. Prompt length is bounded and extra fields are rejected. The prompt is used only for the in-process inference call; request telemetry and summary responses omit prompt and completion content.

## Telemetry record

Each request produces a UUID, UTC timestamp, model/tenant/category identifiers, input and output token counts, TTFT, TPOT, end-to-end latency, success flag, and provenance label. The initial implementation stores records in a bounded process-memory list of the most recent 10,000 requests. A service restart clears it; this store is for the first vertical slice, not durable production telemetry.

Token counts in the simulator use whitespace-separated prompt pieces and output words. They are placeholders, not tokenizer-derived model token counts. All simulator-generated timing fields are explicitly labeled `simulated`.

## Provenance

- `simulated`: produced by the deterministic simulator.
- `measured`: timed by the local HTTP workload client.
- `estimated`: computed from assumptions or pricing inputs (not implemented yet).

Never compare simulated server timing with actual inference measurements as if they were collected on the same backend.
