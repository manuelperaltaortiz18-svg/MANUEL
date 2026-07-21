"""Tests for strategic allocation engine."""
from src.engines.allocation import (
    GROWTH_ALLOCATION,
    BALANCED_ALLOCATION,
    StrategicAllocation,
    AllocationTarget,
)


def test_growth_allocation_sums_to_100():
    assert GROWTH_ALLOCATION.total_weight == 100


def test_balanced_allocation_sums_to_100():
    assert BALANCED_ALLOCATION.total_weight == 100


def test_deviation_calculation():
    actual = {"global_equity": 65, "us_equity": 12, "em_equity": 8, "global_bonds": 10, "reits": 5}
    devs = GROWTH_ALLOCATION.deviation(actual)
    assert devs["global_equity"] == 5.0
    assert devs["us_equity"] == -3.0


def test_needs_rebalance_true():
    actual = {"global_equity": 75, "us_equity": 10, "em_equity": 5, "global_bonds": 5, "reits": 5}
    assert GROWTH_ALLOCATION.needs_rebalance(actual, threshold_pp=5.0)


def test_needs_rebalance_false():
    actual = {"global_equity": 62, "us_equity": 14, "em_equity": 9, "global_bonds": 10, "reits": 5}
    assert not GROWTH_ALLOCATION.needs_rebalance(actual, threshold_pp=5.0)


def test_tactical_range_respects_bounds():
    target = AllocationTarget("equity", 60, 40, 80)
    low, high = target.tactical_range
    assert low >= 40
    assert high <= 80
