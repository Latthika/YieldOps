# Models and Machine Learning

## Implemented and selected

There is still no model downloaded, loaded, fine-tuned, or served. `SimulatedInferenceBackend` is deterministic Python logic and not an ML model. `model_name` in simulation is a label only.

A backend boundary and an optional OpenAI-compatible streaming adapter are implemented. Adapter unit tests use `httpx.MockTransport`; they prove payload parsing and telemetry behavior, not model quality or execution. Model name, max output tokens, temperature, and top-p are passed to a compatible serving endpoint. Actual server token counts are used only when returned; there is no whitespace fallback for real inference.

## Hardware fit and inference research (2026-11-17)

The inspected host is an Apple M4 MacBook Air with 16 GB unified memory, macOS 15.6.1, and native ARM64 Python 3.12.16. `nvidia-smi` and Docker are unavailable; therefore NVIDIA/CUDA benchmarking is not possible here.

The official [MLX installation guide](https://github.com/ml-explore/mlx/blob/main/docs/src/install.rst) states that Apple Silicon, native Python 3.10+, and macOS 14+ are supported, which matches this host. The official [MLX-LM project](https://github.com/ml-explore/mlx-lm) provides model generation on Apple Silicon and notes that large models relative to RAM can be slow. Official [vLLM installation guidance](https://docs.vllm.ai/en/latest/getting_started/installation/cpu/) describes macOS Apple Silicon CPU support as experimental and source-build based; the separate [vLLM-Metal documentation](https://docs.vllm.ai/projects/vllm-metal/en/latest/) describes its MLX-backed Apple GPU plugin.

So real small-model inference is technically plausible on this Mac through MLX/MLX-LM or vLLM-Metal, as a separate Apple Metal experiment. It is not evidence of NVIDIA/CUDA performance. No large inference packages or model files were installed or downloaded because explicit approval is required. The OpenAI-compatible adapter is the integration boundary pending an approved serving runtime and model.

## Forecast and anomaly methods

The project now has two deterministic forecast baselines: last value and 24-hour seasonal naive. A time-aware holdout evaluates these on generated data. The anomaly baseline uses a rolling prior-window median/MAD rule. Neither is trained ML; no real workload series has been collected. Current results should be described as synthetic baseline exercises only.

## Not implemented

No agents or orchestration, actual forecast training, model quality evaluation, LLM evaluation set, tokenizer library, GPU telemetry, optimization, or evidence-backed savings claim exists.
