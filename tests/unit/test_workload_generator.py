"""Tests for synthetic workload helpers."""

import pytest

from yieldops.workload.generator import nearest_rank


def test_nearest_rank_percentiles() -> None:
    assert nearest_rank([4.0, 1.0, 3.0, 2.0], 0.50) == 2.0
    assert nearest_rank([4.0, 1.0, 3.0, 2.0], 0.95) == 4.0


def test_nearest_rank_handles_empty_samples_and_invalid_percentiles() -> None:
    assert nearest_rank([], 0.95) is None
    with pytest.raises(ValueError, match="percentile"):
        nearest_rank([1.0], 0)
