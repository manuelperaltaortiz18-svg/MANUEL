"""Tests for trading data models and instrument arithmetic."""
from datetime import datetime

import pytest

from src.config.trading_config import ES_FUTURE, MES_FUTURE, SP500_CFD
from src.trading.models import Bar, RoundMode, Side, Trade, ExitReason


def test_bar_rejects_inconsistent_ohlc():
    with pytest.raises(ValueError):
        Bar(datetime(2026, 1, 5, 9, 30), open=100, high=99, low=98, close=98.5)
    with pytest.raises(ValueError):
        Bar(datetime(2026, 1, 5, 9, 30), open=100, high=101, low=100.5, close=100.8)


def test_side_sign_and_opposite():
    assert Side.LONG.sign == 1
    assert Side.SHORT.sign == -1
    assert Side.LONG.opposite is Side.SHORT


def test_round_price_respects_tick_grid():
    assert ES_FUTURE.round_price(5000.30) == 5000.25
    assert ES_FUTURE.round_price(5000.30, RoundMode.UP) == 5000.50
    assert ES_FUTURE.round_price(5000.30, RoundMode.DOWN) == 5000.25
    # A price already on the grid must not be nudged by the up/down modes.
    assert ES_FUTURE.round_price(5000.25, RoundMode.UP) == 5000.25
    assert ES_FUTURE.round_price(5000.25, RoundMode.DOWN) == 5000.25


def test_round_qty_floors_to_step_and_enforces_minimum():
    assert MES_FUTURE.round_qty(3.9) == 3.0
    assert MES_FUTURE.round_qty(0.9) == 0.0
    assert SP500_CFD.round_qty(1.77) == 1.7
    assert SP500_CFD.round_qty(0.05) == 0.0


def test_money_conversion_uses_point_value():
    assert ES_FUTURE.money(points=2.0, qty=3) == 300.0
    assert SP500_CFD.money(points=2.0, qty=3) == 6.0


def _trade(gross, commission, risk_points=10.0, qty=1.0, point_value=5.0):
    return Trade(
        symbol="MES",
        side=Side.LONG,
        qty=qty,
        entry_time=datetime(2026, 1, 5, 10, 0),
        entry_price=5000.0,
        exit_time=datetime(2026, 1, 5, 10, 30),
        exit_price=5010.0,
        exit_reason=ExitReason.TAKE_PROFIT,
        gross_pnl=gross,
        commission=commission,
        planned_risk_points=risk_points,
        point_value=point_value,
    )


def test_trade_r_multiple_is_net_of_costs():
    trade = _trade(gross=50.0, commission=0.0)  # 10 pts risk * 1 unit * 5 = 50 risk
    assert trade.r_multiple == pytest.approx(1.0)

    with_costs = _trade(gross=50.0, commission=5.0)
    assert with_costs.r_multiple == pytest.approx(0.9)


def test_trade_net_pnl_and_win_flag():
    trade = _trade(gross=50.0, commission=60.0)
    assert trade.net_pnl == pytest.approx(-10.0)
    assert not trade.is_win
