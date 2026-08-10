"""Tests for position sizing and daily circuit breakers."""
from datetime import date, datetime

import pytest

from src.config.trading_config import MES_FUTURE, SP500_CFD, RiskConfig
from src.trading.models import ExitReason, Side, Trade
from src.trading.risk import RiskManager


def make_manager(instrument=MES_FUTURE, **overrides):
    config = RiskConfig(**overrides) if overrides else RiskConfig()
    manager = RiskManager(config, instrument)
    manager.on_session_start(date(2026, 1, 5), 25_000.0)
    return manager


def closed_trade(net: float) -> Trade:
    return Trade(
        symbol="MES",
        side=Side.LONG,
        qty=1,
        entry_time=datetime(2026, 1, 5, 10, 0),
        entry_price=5000.0,
        exit_time=datetime(2026, 1, 5, 10, 5),
        exit_price=5000.0 + net / 5,
        exit_reason=ExitReason.TAKE_PROFIT if net > 0 else ExitReason.STOP_LOSS,
        gross_pnl=net,
        commission=0.0,
        planned_risk_points=10.0,
        point_value=5.0,
    )


def test_position_size_risks_the_configured_fraction():
    manager = make_manager(risk_per_trade_pct=0.5)
    # 0.5% of 25k = 125 USD budget; a 10pt stop on MES risks 50 USD per contract.
    assert manager.position_size(25_000.0, risk_points=10.0) == 2.0
    assert manager.risk_amount(2.0, 10.0) == pytest.approx(100.0)


def test_position_size_returns_zero_when_min_size_is_too_risky():
    manager = make_manager(risk_per_trade_pct=0.1)  # 25 USD budget
    assert manager.position_size(25_000.0, risk_points=10.0) == 0.0


def test_position_size_supports_fractional_cfd_steps():
    manager = RiskManager(RiskConfig(risk_per_trade_pct=0.5), SP500_CFD)
    # 125 USD budget / (10 pts * 1 USD) = 12.5 units, floored to the 0.1 step.
    assert manager.position_size(25_000.0, risk_points=10.0) == pytest.approx(12.5)


def test_max_units_caps_size():
    manager = make_manager(risk_per_trade_pct=5.0, max_units=3.0)
    assert manager.position_size(25_000.0, risk_points=10.0) == 3.0


def test_daily_trade_cap_blocks_further_entries():
    manager = make_manager(max_trades_per_day=2)
    manager.on_entry_filled()
    assert manager.can_trade(25_000.0)
    manager.on_entry_filled()
    decision = manager.can_trade(25_000.0)
    assert not decision
    assert "daily trade cap" in decision.reason


def test_consecutive_losses_stop_the_day_and_a_win_resets_the_count():
    manager = make_manager(max_consecutive_losses=2, max_trades_per_day=10)
    manager.on_trade_closed(closed_trade(-100))
    assert manager.can_trade(25_000.0)
    manager.on_trade_closed(closed_trade(-100))
    assert not manager.can_trade(25_000.0)

    manager.on_trade_closed(closed_trade(+100))
    assert manager.can_trade(25_000.0)


def test_daily_loss_limit_blocks_trading():
    manager = make_manager(daily_loss_limit_pct=1.0, max_consecutive_losses=99)
    manager.on_trade_closed(closed_trade(-260))  # > 1% of 25k
    decision = manager.can_trade(24_740.0)
    assert not decision
    assert "daily loss limit" in decision.reason


def test_daily_profit_target_stops_trading_when_enabled():
    manager = make_manager(daily_profit_target_pct=1.0)
    manager.on_trade_closed(closed_trade(+260))
    assert not manager.can_trade(25_260.0)


def test_new_session_clears_daily_state():
    manager = make_manager(max_trades_per_day=1)
    manager.on_entry_filled()
    assert not manager.can_trade(25_000.0)
    manager.on_session_start(date(2026, 1, 6), 25_000.0)
    assert manager.can_trade(25_000.0)
