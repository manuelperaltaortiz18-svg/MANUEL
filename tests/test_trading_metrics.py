"""Tests for the performance analytics, especially the 1:1 breakeven maths."""
from datetime import datetime, timedelta

import pytest

from src.trading.metrics import (
    analyse,
    breakeven_hit_rate,
    build_equity_curve,
    daily_pnl,
    hit_rate_confidence_interval,
    max_drawdown,
    optimal_f_note,
    sharpe_ratio,
)
from src.trading.models import ExitReason, Side, Trade

START = datetime(2026, 1, 5, 10, 0)


def trade(
    net,
    day_offset=0,
    risk_points=10.0,
    qty=1.0,
    commission=0.0,
    entry_slippage=0.0,
    exit_slippage=0.0,
):
    entry = START + timedelta(days=day_offset)
    return Trade(
        symbol="MES",
        side=Side.LONG,
        qty=qty,
        entry_time=entry,
        entry_price=5000.0,
        exit_time=entry + timedelta(minutes=30),
        exit_price=5000.0 + net / (qty * 5.0),
        exit_reason=ExitReason.TAKE_PROFIT if net > 0 else ExitReason.STOP_LOSS,
        gross_pnl=net + commission,
        commission=commission,
        planned_risk_points=risk_points,
        point_value=5.0,
        entry_slippage_points=entry_slippage,
        exit_slippage_points=exit_slippage,
    )


def test_breakeven_hit_rate_is_50_percent_for_a_costless_one_to_one():
    assert breakeven_hit_rate(1.0) == pytest.approx(0.5)
    assert breakeven_hit_rate(2.0) == pytest.approx(1 / 3)
    # Costs push the requirement above the coin-flip line.
    assert breakeven_hit_rate(1.0, cost_r=0.04) == pytest.approx(0.52)


def test_analyse_on_an_empty_blotter_is_safe():
    report = analyse([], starting_equity=10_000.0)
    assert report.trades == 0
    assert report.net_pnl == 0.0
    assert report.required_hit_rate_pct == pytest.approx(50.0)


def test_analyse_computes_the_headline_statistics():
    trades = [trade(+50), trade(-50, 1), trade(+50, 2), trade(-50, 3), trade(+50, 4)]
    report = analyse(trades, starting_equity=10_000.0, reward_risk_ratio=1.0)
    assert report.trades == 5
    assert report.wins == 3
    assert report.losses == 2
    assert report.win_rate_pct == pytest.approx(60.0)
    assert report.net_pnl == pytest.approx(50.0)
    assert report.expectancy == pytest.approx(10.0)
    assert report.expectancy_r == pytest.approx(0.2)
    assert report.profit_factor == pytest.approx(1.5)
    assert report.trading_days == 5
    assert report.exit_reasons == {"take_profit": 3, "stop_loss": 2}


def test_costs_raise_the_required_hit_rate_and_shrink_the_edge():
    free = analyse([trade(+50), trade(-50, 1)], 10_000.0)
    costly = analyse(
        [trade(+50, commission=5.0), trade(-50, 1, commission=5.0)], 10_000.0
    )
    assert costly.required_hit_rate_pct > free.required_hit_rate_pct
    assert costly.edge_pct < free.edge_pct


def test_spread_only_costs_still_raise_the_required_hit_rate():
    """A commission-free CFD is not a cost-free CFD: the spread is the cost."""
    spread_only = [
        trade(+50, entry_slippage=0.25, exit_slippage=0.25),
        trade(-50, 1, entry_slippage=0.25, exit_slippage=0.25),
    ]
    report = analyse(spread_only, 10_000.0)
    assert report.commission == 0.0
    assert report.friction == pytest.approx(5.0)  # 0.5 pts * 1 unit * 5 * 2 trades
    assert report.cost_r == pytest.approx(0.05)
    assert report.required_hit_rate_pct == pytest.approx(52.5)


def test_equity_curve_and_drawdown():
    trades = [trade(+100), trade(-300, 1), trade(+50, 2)]
    curve = build_equity_curve(trades, 1_000.0)
    assert curve == [1_000.0, 1_100.0, 800.0, 850.0]
    drop, pct = max_drawdown(curve)
    assert drop == pytest.approx(300.0)
    assert pct == pytest.approx(300 / 1100 * 100)


def test_daily_pnl_groups_by_exit_date():
    trades = [trade(+10), trade(-4), trade(+7, 1)]
    daily = daily_pnl(trades)
    assert len(daily) == 2
    assert daily[START.date()] == pytest.approx(6.0)


def test_sharpe_is_zero_without_variation_or_history():
    assert sharpe_ratio([10.0], 10_000.0) == 0.0
    assert sharpe_ratio([10.0, 10.0, 10.0], 10_000.0) == 0.0
    assert sharpe_ratio([10.0, -5.0, 20.0], 10_000.0) > 0


def test_hit_rate_confidence_interval_widens_on_small_samples():
    low_small, high_small = hit_rate_confidence_interval(12, 20)
    low_big, high_big = hit_rate_confidence_interval(600, 1000)
    assert (high_small - low_small) > (high_big - low_big)
    assert 0.0 <= low_small <= high_small <= 1.0


def test_small_sample_warning_is_emitted():
    small = analyse([trade(+50), trade(-50, 1)], 10_000.0)
    assert optimal_f_note(small) is not None
    small.trades = 500
    assert optimal_f_note(small) is None


def test_summary_renders_without_crashing():
    report = analyse([trade(+50), trade(-50, 1)], 10_000.0)
    text = report.summary()
    assert "Win rate" in text and "Max drawdown" in text
