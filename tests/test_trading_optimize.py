"""Tests for the walk-forward optimiser and its overfitting guards."""
from datetime import date, datetime, time, timedelta

import pytest

from src.trading.metrics import PerformanceReport
from src.trading.models import Bar
from src.trading.optimize import (
    Candidate,
    OptimizationOutcome,
    best_of_n_by_chance,
    grid_size,
    iter_param_sets,
    optimise,
    split_by_session,
)


def bars_over(sessions: int) -> list[Bar]:
    out = []
    day = date(2026, 1, 5)
    made = 0
    while made < sessions:
        if day.weekday() < 5:
            ts = datetime.combine(day, time(9, 30))
            for _ in range(4):
                out.append(Bar(ts, 100, 101, 99, 100))
                ts += timedelta(minutes=15)
            made += 1
        day += timedelta(days=1)
    return out


def report(trades: int, expectancy_r: float, win_rate: float = 50.0) -> PerformanceReport:
    return PerformanceReport(
        trades=trades, expectancy_r=expectancy_r, win_rate_pct=win_rate
    )


def test_grid_expands_to_every_combination():
    grid = {"a": (1, 2), "b": ("x", "y", "z")}
    combos = list(iter_param_sets(grid))
    assert len(combos) == 6 == grid_size(grid)
    assert {"a": 1, "b": "x"} in combos
    assert {"a": 2, "b": "z"} in combos


def test_an_empty_grid_yields_one_default_run():
    assert list(iter_param_sets({})) == [{}]
    assert grid_size({}) == 1


def test_the_split_lands_on_a_session_boundary():
    """Splitting mid-session would tune on a day's open and trade its close."""
    bars = bars_over(10)
    in_sample, out_sample = split_by_session(bars, 0.6)
    in_days = {b.timestamp.date() for b in in_sample}
    out_days = {b.timestamp.date() for b in out_sample}
    assert in_days and out_days
    assert not (in_days & out_days)  # no day appears on both sides
    assert max(in_days) < min(out_days)
    assert len(in_sample) + len(out_sample) == len(bars)


def test_the_split_rejects_impossible_fractions():
    bars = bars_over(10)
    with pytest.raises(ValueError):
        split_by_session(bars, 0.0)
    with pytest.raises(ValueError):
        split_by_session(bars, 1.0)


def test_a_single_session_cannot_be_split():
    with pytest.raises(ValueError):
        split_by_session(bars_over(1), 0.6)


def test_candidates_are_ranked_and_rescored_out_of_sample():
    bars = bars_over(20)
    grid = {"knob": (1, 2, 3)}

    def evaluate(subset, params):
        in_sample = len({b.timestamp.date() for b in subset}) > 8
        # knob=2 looks best in-sample and collapses out-of-sample.
        if params["knob"] == 2:
            return report(50, 0.30 if in_sample else -0.20)
        return report(50, 0.05)

    outcome = optimise(bars, grid, evaluate, min_trades=10, top=3)
    assert outcome.combinations_tested == 3
    assert outcome.best.params == {"knob": 2}
    assert outcome.best.in_sample_score == pytest.approx(0.30)
    assert outcome.best.out_sample_score == pytest.approx(-0.20)
    assert outcome.best.degradation < 0


def test_candidates_without_enough_trades_are_dropped():
    bars = bars_over(20)

    def evaluate(subset, params):
        return report(5 if params["knob"] == 1 else 50, 0.1)

    outcome = optimise(bars, {"knob": (1, 2)}, evaluate, min_trades=20)
    assert [c.params for c in outcome.candidates] == [{"knob": 2}]


def test_the_chance_benchmark_rises_with_the_number_of_trials():
    few = best_of_n_by_chance(2, 100, simulations=800)
    many = best_of_n_by_chance(200, 100, simulations=800)
    assert 0.5 < few < many < 1.0


def test_the_chance_benchmark_falls_as_the_sample_grows():
    """More trades means less room for luck to move the hit rate."""
    small = best_of_n_by_chance(20, 40, simulations=800)
    large = best_of_n_by_chance(20, 2000, simulations=800)
    assert small > large > 0.5


def test_the_chance_benchmark_is_deterministic():
    assert best_of_n_by_chance(10, 100, simulations=400, seed=3) == (
        best_of_n_by_chance(10, 100, simulations=400, seed=3)
    )


def test_a_result_that_loses_out_of_sample_is_called_overfitting():
    outcome = OptimizationOutcome(
        candidates=[Candidate({}, report(100, 0.4, 70.0), report(100, -0.1, 45.0))],
        combinations_tested=10,
        chance_hit_rate=0.55,
    )
    assert "overfitting" in outcome.verdict()


def test_a_result_no_better_than_luck_is_called_noise():
    outcome = OptimizationOutcome(
        candidates=[Candidate({}, report(100, 0.05, 52.0), report(100, 0.02, 51.0))],
        combinations_tested=50,
        chance_hit_rate=0.58,
    )
    assert "noise" in outcome.verdict()


def test_a_thin_out_of_sample_refuses_to_conclude():
    outcome = OptimizationOutcome(
        candidates=[Candidate({}, report(100, 0.4, 70.0), report(12, 0.3, 65.0))],
        combinations_tested=10,
        chance_hit_rate=0.55,
    )
    assert "too few" in outcome.verdict()


def test_a_surviving_result_still_asks_for_confirmation():
    outcome = OptimizationOutcome(
        candidates=[Candidate({}, report(200, 0.30, 65.0), report(120, 0.25, 63.0))],
        combinations_tested=10,
        chance_hit_rate=0.55,
    )
    verdict = outcome.verdict()
    assert "Survives" in verdict and "confirm" in verdict


def test_an_empty_search_says_so():
    assert "No candidate" in OptimizationOutcome().verdict()


def test_the_null_rate_follows_the_payoff():
    """
    With no edge a 1:2 bracket wins a third of the time, not half. Judging a
    1:2 search against a 50% coin would set an impossibly high bar and reject
    a real edge.
    """
    coin = best_of_n_by_chance(20, 400, simulations=800, null_rate=0.5)
    one_to_two = best_of_n_by_chance(20, 400, simulations=800, null_rate=1 / 3)
    assert one_to_two < coin
    assert 1 / 3 < one_to_two < 0.45


def test_the_null_rate_must_be_a_probability():
    with pytest.raises(ValueError):
        best_of_n_by_chance(10, 100, null_rate=1.5)


def test_the_optimiser_uses_the_payoff_aware_null():
    bars = bars_over(20)

    def evaluate(subset, params):
        return report(200, 0.1, 45.0)

    coin = optimise(bars, {"k": (1, 2)}, evaluate, min_trades=10, reward_risk=1.0)
    rr2 = optimise(bars, {"k": (1, 2)}, evaluate, min_trades=10, reward_risk=2.0)
    assert rr2.chance_hit_rate < coin.chance_hit_rate
