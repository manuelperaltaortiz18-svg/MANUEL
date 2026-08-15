"""Tests for the prop-firm challenge simulator."""
import pytest

from src.trading.propfirm import (
    ChallengeRules,
    StrategyStats,
    probability_of_return,
    required_hit_rate_for_return,
    simulate_challenge,
)


def test_breakeven_hit_rate_matches_the_one_to_one_arithmetic():
    assert StrategyStats(hit_rate=0.5).breakeven_hit_rate == pytest.approx(0.5)
    assert StrategyStats(hit_rate=0.5, cost_r=0.12).breakeven_hit_rate == pytest.approx(0.56)


def test_expectancy_is_negative_below_the_breakeven_line():
    losing = StrategyStats(hit_rate=0.52, cost_r=0.12)
    assert losing.expectancy_r < 0
    winning = StrategyStats(hit_rate=0.60, cost_r=0.12)
    assert winning.expectancy_r > 0


def test_hit_rate_must_be_a_probability():
    with pytest.raises(ValueError):
        StrategyStats(hit_rate=1.4)


def test_a_negative_edge_almost_never_passes_a_challenge():
    losing = StrategyStats(hit_rate=0.50, cost_r=0.12, trades_per_day=2)
    outcome = simulate_challenge(losing, risk_per_trade_pct=1.0, trials=2_000)
    assert outcome.pass_rate < 0.25
    assert outcome.failure_rate > outcome.pass_rate


def test_a_real_edge_passes_more_often_than_it_blows_up():
    winning = StrategyStats(hit_rate=0.62, cost_r=0.12, trades_per_day=2)
    outcome = simulate_challenge(winning, risk_per_trade_pct=1.0, trials=2_000)
    assert outcome.pass_rate > outcome.failure_rate
    assert outcome.median_days_to_pass > 0


def test_oversizing_raises_the_blow_up_rate():
    """The core trap: bigger size does not mean a better chance of passing."""
    stats = StrategyStats(hit_rate=0.58, cost_r=0.12, trades_per_day=2)
    small = simulate_challenge(stats, risk_per_trade_pct=0.5, trials=2_000)
    large = simulate_challenge(stats, risk_per_trade_pct=3.0, trials=2_000)
    assert large.failure_rate > small.failure_rate


def test_trailing_drawdown_is_harsher_than_a_static_one():
    stats = StrategyStats(hit_rate=0.55, cost_r=0.12)
    trailing = simulate_challenge(
        stats, 1.0, ChallengeRules(trailing_drawdown=True), trials=2_000
    )
    static = simulate_challenge(
        stats, 1.0, ChallengeRules(trailing_drawdown=False), trials=2_000
    )
    assert trailing.failed_drawdown >= static.failed_drawdown


def test_outcomes_account_for_every_trial():
    outcome = simulate_challenge(StrategyStats(hit_rate=0.55), 1.0, trials=1_500)
    total = (
        outcome.passed
        + outcome.failed_daily
        + outcome.failed_drawdown
        + outcome.ran_out_of_time
    )
    assert total == outcome.trials


def test_simulation_is_deterministic_for_a_given_seed():
    a = simulate_challenge(StrategyStats(hit_rate=0.56), 1.0, trials=800, seed=3)
    b = simulate_challenge(StrategyStats(hit_rate=0.56), 1.0, trials=800, seed=3)
    assert a.passed == b.passed and a.failed_drawdown == b.failed_drawdown


def test_probability_of_a_large_return_also_reports_ruin():
    stats = StrategyStats(hit_rate=0.56, cost_r=0.12, trades_per_day=2)
    reached, ruined = probability_of_return(stats, 1.0, target_return_pct=70.0, trials=2_000)
    assert 0.0 <= reached <= 1.0
    assert 0.0 <= ruined <= 1.0
    assert reached + ruined <= 1.0


def test_required_hit_rate_rises_with_the_target():
    modest = required_hit_rate_for_return(10.0, 0.5, trades=500, cost_r=0.12)
    ambitious = required_hit_rate_for_return(70.0, 0.5, trades=500, cost_r=0.12)
    assert modest is not None and ambitious is not None
    assert ambitious > modest > 0.5


def test_impossible_targets_return_none():
    # 500% on 20 trades at 0.5% risk cannot happen at any hit rate.
    assert required_hit_rate_for_return(500.0, 0.5, trades=20, cost_r=0.12) is None


# ---------------------------------------------------------------------------
#  Year outcomes and sample-size requirements
# ---------------------------------------------------------------------------

from src.trading.propfirm import simulate_year, trades_needed_to_detect  # noqa: E402


def test_a_one_to_two_payoff_breaks_even_at_a_third():
    """The whole appeal of 1:2 — the hit rate hurdle drops from 50% to 33%."""
    assert StrategyStats(hit_rate=0.4, reward_risk=2.0).breakeven_hit_rate == pytest.approx(
        1 / 3
    )
    assert StrategyStats(hit_rate=0.4, reward_risk=2.0, cost_r=0.06).breakeven_hit_rate == (
        pytest.approx(1.06 / 3)
    )


def test_a_better_edge_shifts_the_whole_distribution_up():
    weak = simulate_year(StrategyStats(0.36, reward_risk=2.0, cost_r=0.05), 1.0, trials=800)
    strong = simulate_year(StrategyStats(0.46, reward_risk=2.0, cost_r=0.05), 1.0, trials=800)
    assert strong.median_return_pct > weak.median_return_pct
    assert strong.prob_target_pct > weak.prob_target_pct
    assert strong.prob_loss_pct < weak.prob_loss_pct


def test_the_reported_band_is_ordered_and_wide():
    outcome = simulate_year(StrategyStats(0.42, reward_risk=2.0, cost_r=0.05), 1.0, trials=800)
    assert outcome.p10_return_pct < outcome.median_return_pct < outcome.p90_return_pct
    assert outcome.median_max_dd_pct > 0
    assert outcome.worst_max_dd_pct >= outcome.median_max_dd_pct
    assert outcome.trades == 500  # 2 per day over 250 sessions


def test_bigger_size_raises_both_the_return_and_the_drawdown():
    stats = StrategyStats(0.42, reward_risk=2.0, cost_r=0.05)
    small = simulate_year(stats, 0.5, trials=800)
    large = simulate_year(stats, 2.0, trials=800)
    assert large.median_return_pct > small.median_return_pct
    assert large.median_max_dd_pct > small.median_max_dd_pct


def test_a_losing_edge_loses_most_years():
    outcome = simulate_year(StrategyStats(0.30, reward_risk=2.0, cost_r=0.05), 1.0, trials=800)
    assert outcome.median_return_pct < 0
    assert outcome.prob_loss_pct > 60


def test_sample_size_grows_as_the_edge_shrinks():
    wide = trades_needed_to_detect(0.50, 0.35)
    narrow = trades_needed_to_detect(0.38, 0.35)
    assert narrow > wide > 0


def test_an_edge_of_zero_can_never_be_detected():
    assert trades_needed_to_detect(0.35, 0.35) is None


def test_sample_size_rejects_non_probabilities():
    with pytest.raises(ValueError):
        trades_needed_to_detect(1.4, 0.35)
