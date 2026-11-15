# Datasets and Data Provenance Audit

## Repository datasets

There are **no dataset files** in the repository. `datasets/synthetic/.gitkeep` is an empty directory placeholder (0 bytes), not a dataset. No public dataset was downloaded or included.

## Runtime-generated inputs

`src/yieldops/workload/generator.py` defines four short, fixed prompt templates with categories: structured extraction, classification, summarization, and question answering. At runtime, the runner prepends a deterministic request index (`Synthetic request N:`) and sends the input to the local YieldOps API. These are synthetic examples embedded in source code; they have no external source or licensing provenance.

`tests/integration/test_inference_workflow.py` and `tests/unit/test_simulator.py` contain additional short synthetic test strings. They exist only as test fixtures.

## Runtime data volume and retention

- Workload run recorded in `docs/EXPERIMENTS.md`: 20 requests at concurrency 4. The script printed a summary; it does not save a dataset file.
- Per-request API telemetry: UUID, timestamp, model/tenant/category labels, whitespace-based input/output counts, latency fields, success, provenance. It omits prompt and completion text.
- Runtime store: at most 10,000 recent telemetry objects in process memory; lost on restart.
- There is no persistent request log, Parquet/CSV/JSONL dataset, feature table, or model-training corpus.

## Training, validation, and benchmark use

No model is trained or fine-tuned. No train/validation/test split exists. The 10 pytest cases validate software contracts and formulas; they are not model evaluation data. The 20-request smoke run validates API/workload integration only. It is not a quality benchmark and does not establish GPU performance.

## External data sources

The application has no external data-source integration. The workload runner calls the configured HTTP API URL (default loopback). It does not call Hugging Face, a model API, cloud billing, or a telemetry vendor. The GitHub integration is development workflow tooling and is not part of the running application.

## Provenance rules for future datasets

Before adding data, record source URL/license, collection date, schema, row count, transformations, split method, and whether examples are synthetic or real. Do not imply that generated prompts represent a validated task benchmark. Do not store actual user prompts or responses without a justified and approved data-handling design.
