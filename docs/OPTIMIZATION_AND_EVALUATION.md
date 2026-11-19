# Workload Intelligence, Cost, and Evaluation

## Implemented for Milestone 3

- `profile_telemetry` summarizes the bounded retained sample overall and by model/task category: request volume, per-minute traffic counts and peak, success/failure, known token counts, latency percentiles, and throughput when timestamps span a non-zero interval.
- `estimate_token_cost` calculates provider-style token charges from explicit, caller-supplied per-model input/output USD per 1,000 token rates. It reports priced/unpriced request counts and aggregates by model, workload category, and tenant. Results are always `estimated`.
- `detect_high_latency` uses a rolling prior-window median and median absolute deviation; it can be inspected at `GET /v1/telemetry/anomalies`.
- `forecasting/baselines.py` implements last-value and seasonal-naive baselines and MAE/RMSE. A deterministic experiment uses a time-aware split.

## Cost formulas and limits

For each priced request:

```text
estimated request cost = input_tokens / 1000 * configured_input_rate
                       + output_tokens / 1000 * configured_output_rate
```

Rates are supplied in the `POST /v1/telemetry/cost-estimate` request body and keyed by the stored model label. A request is unpriced when its rate or either token count is missing. Cost output includes the configured rate card so an estimate can be audited and recalculated. It does not infer cloud billing, GPU-hours, idle spend, or allocated infrastructure cost. No savings result is calculated.

## Anomaly and forecast evaluation

The anomaly experiment compares a rolling median/MAD detector with a rolling mean plus three standard deviations against injected synthetic outliers. Both returned precision and recall 1.0 on the simple synthetic set; that is a test of implementation behavior, not validated operational performance.

The forecast experiment uses 504 earlier synthetic hourly values for history and the next 168 values as holdout. The 24-hour seasonal-naive baseline beat the last-value baseline on MAE and RMSE in that generated series. No model is trained, no measured workload has been collected, and the result does not demonstrate capacity-planning utility.

## Storage decision

PostgreSQL was evaluated and not introduced. The current project is a single-process learning prototype, the retained 10,000-record sample is enough for endpoint demonstrations, and adding a database would create migration/service/credential work without improving the synthetic experiments. The tradeoff is explicit: restart loses records and workers do not share telemetry. Revisit PostgreSQL before long-running experiments, multi-worker service use, or historical production profiling.

## Not implemented

There is no search/optimization engine, candidate comparison, quality constraint, GPU allocation policy, real billing data, or cost-saving claim. Agents remain reserved for the later agent-engineering milestone.
