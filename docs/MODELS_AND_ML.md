# Models and Machine Learning: Current State

## Model inventory

| Role | Actual implementation | Status |
|---|---|---|
| LLM for agent reasoning | None | No agents or LLM client exist. |
| Inference model monitored by YieldOps | None | The API accepts a `model_name` label but does not load or call a model. |
| Forecasting/anomaly/optimization ML | None | No trained, pretrained, or classical ML estimator is present. |
| Test simulator | `SimulatedInferenceBackend` | Deterministic Python rules, not a learned model. |

## Simulator details

`src/yieldops/inference/simulator.py` counts input tokens using Python whitespace splitting, returns the fixed string `simulated completion`, and computes:

- `TTFT = 20 ms + 0.5 ms × whitespace-piece count`
- `TPOT = 10 ms` when output is non-empty
- `end_to_end = TTFT + (output_count - 1) × TPOT`

The simulator has no architecture, weights, tokenizer, training data, loss function, optimizer, or model-quality metric. Its generated output is not a language-model response. The `model_name` request field is metadata only.

## Training and inference

YieldOps does **not** train an LLM. It does not currently use an existing LLM through an API or local runtime either. No PyTorch, Transformers, vLLM, MLX, or model SDK is imported by the application. PyTorch availability on the development host is unrelated to the runtime implementation.

## Evaluation evidence

The test suite verifies deterministic formulas and API behavior. It has no accuracy, F1, schema-quality, reference-generation, or LLM-as-judge evaluation. No model output quality has been measured. No efficiency improvement is established.

## Candidate models (future options, not selections)

Once hardware, license, task, and quality targets are established, candidates could include a small open-weight instruction model served by a compatible engine on an approved GPU host. Apple Silicon MLX/vLLM-Metal could be explored as a distinct local path. Forecasting should begin with statistical baselines before comparing scikit-learn or other regressors. None of these options has been installed, benchmarked, or selected in this repository.
