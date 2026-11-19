"""Tests for dependency-free demand forecasting baselines."""

import pytest

from yieldops.forecasting.baselines import (
    last_value_forecast,
    mean_absolute_error,
    root_mean_squared_error,
    seasonal_naive_forecast,
)


def test_forecasts_are_built_from_training_history_only() -> None:
    history = [1.0, 2.0, 3.0, 4.0]

    assert last_value_forecast(history, 3) == [4.0, 4.0, 4.0]
    assert seasonal_naive_forecast(history, period=2, horizon=5) == [3.0, 4.0, 3.0, 4.0, 3.0]
    assert mean_absolute_error([2, 4], [1, 6]) == 1.5
    assert root_mean_squared_error([2, 4], [1, 6]) == pytest.approx(1.5811388)


def test_forecast_helpers_reject_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="empty"):
        last_value_forecast([], 1)
    with pytest.raises(ValueError, match="seasonal period"):
        seasonal_naive_forecast([1], period=2, horizon=1)
    with pytest.raises(ValueError, match="same non-zero length"):
        mean_absolute_error([1], [])
