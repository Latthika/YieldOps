"""Generate and evaluate deterministic synthetic forecasting/anomaly baselines."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import fmean, stdev
from uuid import uuid4

from yieldops.common.schemas import InferenceTelemetry, MetricProvenance, TaskCategory
from yieldops.evaluation.anomaly import detect_high_latency
from yieldops.forecasting.baselines import (
    last_value_forecast,
    mean_absolute_error,
    root_mean_squared_error,
    seasonal_naive_forecast,
)

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
PERIODS = 24 * 28
HORIZON = 24 * 7


def generate_demand(seed: int = SEED, periods: int = PERIODS) -> list[int]:
    """Create explicitly synthetic hourly demand with trend, cycles and noise."""
    rng = random.Random(seed)
    values = []
    for index in range(periods):
        hour = index % 24
        weekly = index % (24 * 7)
        demand = (
            100
            + 24 * math.sin(2 * math.pi * hour / 24)
            + 8 * math.sin(2 * math.pi * weekly / (24 * 7))
            + 0.04 * index
            + rng.gauss(0, 4)
        )
        values.append(max(0, round(demand)))
    return values


def evaluate_anomalies(seed: int = SEED, count: int = 240) -> dict[str, object]:
    """Compare the rolling MAD detector with a rolling mean plus three sigma."""
    rng = random.Random(seed + 1)
    labels = [False] * count
    latencies = [50 + rng.gauss(0, 3) for _ in range(count)]
    for index, value in ((60, 100), (140, 115), (210, 105)):
        if index < count:
            labels[index] = True
            latencies[index] = value

    timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)
    records = [
        InferenceTelemetry(
            request_id=uuid4(),
            timestamp_utc=timestamp + timedelta(minutes=index),
            model_name="synthetic-baseline",
            tenant_id=None,
            task_category=TaskCategory.OTHER,
            input_tokens=10,
            output_tokens=8,
            token_count_provenance=MetricProvenance.SIMULATED,
            ttft_ms=value / 2,
            tpot_ms=value / 16,
            end_to_end_latency_ms=value,
            output_tokens_per_second=8 * 1_000 / value,
            success=True,
            provenance=MetricProvenance.SIMULATED,
        )
        for index, value in enumerate(latencies)
    ]
    mad_ids = {record.request_id for record in detect_high_latency(records, window_size=24)}
    mad_predictions = [record.request_id in mad_ids for record in records]
    mean_predictions = [False] * count
    for index in range(24, count):
        prior = latencies[index - 24 : index]
        mean_predictions[index] = latencies[index] > fmean(prior) + 3 * stdev(prior)
    return {
        "synthetic_anomalies": sum(labels),
        "rolling_median_mad": _classification_metrics(labels, mad_predictions),
        "rolling_mean_plus_3_sigma": _classification_metrics(labels, mean_predictions),
    }


def _classification_metrics(labels: list[bool], predictions: list[bool]) -> dict[str, float | int]:
    tp = sum(label and prediction for label, prediction in zip(labels, predictions))
    fp = sum(not label and prediction for label, prediction in zip(labels, predictions))
    fn = sum(label and not prediction for label, prediction in zip(labels, predictions))
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
    }


def run(output_root: Path = ROOT) -> dict[str, object]:
    config = {
        "provenance": "synthetic",
        "seed": SEED,
        "forecast": {
            "frequency": "hourly",
            "periods": PERIODS,
            "train_periods": PERIODS - HORIZON,
            "test_periods": HORIZON,
            "seasonal_period": 24,
            "target": "synthetic request count",
            "candidates": ["last value", "24-hour seasonal naive"],
        },
        "anomaly": {
            "records": 240,
            "baseline_window": 24,
            "mad_threshold": 3.5,
            "injected_anomaly_indexes": [60, 140, 210],
            "comparison": "rolling mean + 3 sample standard deviations",
        },
    }
    configs_dir = output_root / "experiments" / "configs"
    results_dir = output_root / "experiments" / "results"
    data_dir = output_root / "datasets" / "synthetic"
    configs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    (configs_dir / "milestone_3_baselines.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n"
    )

    values = generate_demand()
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dataset_path = data_dir / "workload_demand_hourly.csv"
    with dataset_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("timestamp_utc", "request_count", "provenance", "seed"))
        for index, value in enumerate(values):
            writer.writerow(
                ((start + timedelta(hours=index)).isoformat(), value, "synthetic", SEED)
            )

    train, test = values[:-HORIZON], values[-HORIZON:]
    forecasts = {
        "last_value": last_value_forecast(train, HORIZON),
        "seasonal_naive_24": seasonal_naive_forecast(
            train, period=24, horizon=HORIZON
        ),
    }
    forecast_results = {
        name: {
            "mae_requests": mean_absolute_error(test, prediction),
            "rmse_requests": root_mean_squared_error(test, prediction),
        }
        for name, prediction in forecasts.items()
    }
    results = {
        "config": config,
        "dataset": str(dataset_path.relative_to(output_root)),
        "dataset_rows": len(values),
        "time_aware_split": {
            "train_rows": len(train),
            "test_rows": len(test),
            "train_before_test": True,
        },
        "forecast": forecast_results,
        "anomaly": evaluate_anomalies(),
        "limitations": [
            "All generated demand and latency records are synthetic.",
            "Forecast scores do not establish production usefulness.",
            "The detector is a simple baseline evaluated on injected anomalies.",
        ],
    }
    (results_dir / "milestone_3_baselines.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    _write_report(results_dir / "milestone_3_baselines.md", results)
    return results


def _write_report(path: Path, results: dict[str, object]) -> None:
    forecast = results["forecast"]
    anomaly = results["anomaly"]
    assert isinstance(forecast, dict) and isinstance(anomaly, dict)
    lines = [
        "# Milestone 3 Synthetic Baseline Experiment",
        "",
        "This report was generated by `scripts/run_milestone_experiments.py`.",
        "All input demand and anomaly labels are synthetic; this is not production evidence.",
        "",
        "## Forecasting",
        "",
        f"Dataset: `{results['dataset']}` ({results['dataset_rows']} hourly rows).",
        f"Time-ordered split: {results['time_aware_split']['train_rows']} train rows, "
        f"then {results['time_aware_split']['test_rows']} test rows.",
        "No test observations are used to build the forecast.",
        "",
        "| Method | MAE (requests) | RMSE (requests) |",
        "|---|---:|---:|",
    ]
    for name, scores in forecast.items():
        lines.append(
            f"| {name} | {scores['mae_requests']:.3f} | {scores['rmse_requests']:.3f} |"
        )
    lines += ["", "## Anomaly detection", "", "Synthetic injected outliers: 3.", ""]
    lines.append("| Method | TP | FP | FN | Precision | Recall |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for name, scores in anomaly.items():
        if name == "synthetic_anomalies":
            continue
        lines.append(
            f"| {name} | {scores['true_positives']} | {scores['false_positives']} | "
            f"{scores['false_negatives']} | {scores['precision']:.3f} | {scores['recall']:.3f} |"
        )
    lines += [
        "",
        "## Reproduction",
        "",
        "Run `uv run python scripts/run_milestone_experiments.py` from the project root.",
        "The seed and split parameters are recorded in `experiments/configs/milestone_3_baselines.json`.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in results["limitations"]],
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.output_root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
