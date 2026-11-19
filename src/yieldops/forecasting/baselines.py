"""Small dependency-free time-series baselines for reproducible experiments."""

from collections.abc import Sequence
from math import sqrt


def last_value_forecast(history: Sequence[float], horizon: int) -> list[float]:
    """Repeat the most recent observed value for every future step."""
    _validate(history, horizon)
    return [history[-1]] * horizon


def seasonal_naive_forecast(
    history: Sequence[float], *, period: int, horizon: int
) -> list[float]:
    """Repeat the final observed seasonal cycle over the forecast horizon."""
    _validate(history, horizon)
    if period < 1 or len(history) < period:
        raise ValueError("history must contain at least one complete seasonal period")
    cycle = history[-period:]
    return [cycle[index % period] for index in range(horizon)]


def mean_absolute_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    _validate_pair(actual, predicted)
    return sum(abs(left - right) for left, right in zip(actual, predicted)) / len(actual)


def root_mean_squared_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    _validate_pair(actual, predicted)
    return sqrt(sum((left - right) ** 2 for left, right in zip(actual, predicted)) / len(actual))


def _validate(history: Sequence[float], horizon: int) -> None:
    if not history:
        raise ValueError("history cannot be empty")
    if horizon < 1:
        raise ValueError("horizon must be positive")


def _validate_pair(actual: Sequence[float], predicted: Sequence[float]) -> None:
    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same non-zero length")

