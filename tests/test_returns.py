"""Tests for return analysis."""
import math
from src.analysis.returns import (
    cagr,
    compute_rolling_returns,
    compute_drawdowns,
    missed_best_days_impact,
)


def test_cagr_basic():
    result = cagr(100, 200, 10)
    assert abs(result - 0.07177) < 0.001


def test_cagr_zero_years():
    assert cagr(100, 200, 0) == 0.0


def test_rolling_returns_insufficient_data():
    prices = [(f"2020-01-{i:02d}", 100 + i) for i in range(1, 10)]
    stats = compute_rolling_returns(prices, 1)
    assert stats.count == 0


def test_drawdowns_simple():
    prices = [
        ("2020-01-01", 100),
        ("2020-02-01", 110),
        ("2020-03-01", 85),  # -22.7% from peak
        ("2020-04-01", 95),
        ("2020-05-01", 115),  # recovery
    ]
    events = compute_drawdowns(prices, threshold_pct=-0.15)
    assert len(events) == 1
    assert events[0].max_drawdown_pct < -0.20


def test_missed_best_days():
    daily = [0.01, -0.005, 0.02, -0.01, 0.015, 0.005, -0.008, 0.012] * 30
    result = missed_best_days_impact(daily, [5, 10])
    assert result[0] > result[5] > result[10]
