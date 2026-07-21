"""Tests for compounding calculations."""
import pytest
from src.core.compounding import (
    future_value,
    real_future_value,
    cost_drag,
    cost_drag_table,
    one_pct_matters,
    compounding_scenarios,
    spain_capital_gains_tax,
    after_tax_compounded_wealth,
)


def test_future_value_no_contributions():
    fv = future_value(100_000, 0.07, 40)
    assert fv > 1_400_000
    assert fv < 1_600_000


def test_future_value_with_contributions():
    fv = future_value(100_000, 0.07, 40, monthly_contribution=500)
    assert fv > future_value(100_000, 0.07, 40)


def test_real_future_value():
    nominal = 1_000_000
    real = real_future_value(nominal, 0.02, 40)
    assert real < nominal
    assert real > 400_000


def test_cost_drag_positive():
    drag = cost_drag(100_000, 0.07, 0.20, 40)
    assert drag > 0


def test_cost_drag_zero_ter():
    drag = cost_drag(100_000, 0.07, 0.0, 40)
    assert drag == 0.0


def test_cost_drag_table_keys():
    table = cost_drag_table(100_000, 0.07, 0.20)
    assert set(table.keys()) == {10, 20, 30, 40}
    assert all(v >= 0 for v in table.values())
    assert table[40] > table[10]


def test_one_pct_matters():
    result = one_pct_matters(100_000, 0.07, 40)
    assert len(result) == 6
    assert result["+1.0%"] > 0
    assert result["-1.0%"] < 0


def test_compounding_scenarios():
    results = compounding_scenarios(100_000)
    assert "conservative" in results
    assert "optimistic" in results
    assert 40 in results["base"]
    assert results["optimistic"][40].future_value_nominal > results["conservative"][40].future_value_nominal


def test_spain_tax_zero_gain():
    assert spain_capital_gains_tax(0) == 0.0
    assert spain_capital_gains_tax(-1000) == 0.0


def test_spain_tax_first_bracket():
    tax = spain_capital_gains_tax(5_000)
    assert tax == 5_000 * 0.19


def test_spain_tax_multi_bracket():
    tax = spain_capital_gains_tax(50_000)
    expected = 6_000 * 0.19 + (50_000 - 6_000) * 0.21
    assert tax == expected


def test_after_tax_hold_vs_periodic():
    result = after_tax_compounded_wealth(100_000, 0.07, 40, realization_frequency_years=5)
    assert "after_tax_hold" in result
    assert "after_tax_periodic" in result
    assert result["after_tax_hold"] > result["after_tax_periodic"]
    assert result["tax_drag"] > 0
