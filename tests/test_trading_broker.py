"""Tests for the simulated matching engine's fill assumptions."""
from datetime import datetime, timedelta

import pytest

from src.config.trading_config import MES_FUTURE
from src.trading.broker import SimulatedBroker
from src.trading.models import Bar, ExitReason, InstrumentSpec, Side

NO_COST = InstrumentSpec(
    symbol="TEST",
    tick_size=0.25,
    point_value=5.0,
    commission_per_unit=0.0,
    slippage_ticks=0.0,
)

T0 = datetime(2026, 1, 5, 9, 30)


def bar(index, o, h, l, c):
    return Bar(T0 + timedelta(minutes=5 * index), o, h, l, c)


def armed_broker(instrument=NO_COST, side=Side.LONG):
    broker = SimulatedBroker(instrument, starting_equity=10_000.0)
    if side is Side.LONG:
        broker.submit_bracket(Side.LONG, 1, 5010.0, 5000.0, 5020.0, T0)
    else:
        broker.submit_bracket(Side.SHORT, 1, 4990.0, 5000.0, 4980.0, T0)
    return broker


def test_entry_does_not_fill_without_touching_the_level():
    broker = armed_broker()
    broker.on_bar(bar(1, 5000, 5009.75, 4995, 5005))
    assert broker.position is None
    assert broker.pending_order is not None


def test_entry_fills_at_the_stop_level_when_price_trades_through():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5015, 5004, 5012))
    assert broker.position is not None
    assert broker.position.entry_price == 5010.0


def test_gapped_entry_fills_at_the_open_not_the_level():
    broker = armed_broker()
    broker.on_bar(bar(1, 5013, 5016, 5012, 5015))
    assert broker.position.entry_price == 5013.0


def test_stop_limit_skips_entries_that_gap_beyond_the_limit():
    broker = SimulatedBroker(NO_COST, starting_equity=10_000.0)
    broker.submit_bracket(
        Side.LONG, 1, 5010.0, 5000.0, 5020.0, T0, entry_limit=5011.0
    )
    broker.on_bar(bar(1, 5013, 5016, 5012, 5015))  # opens 3 pts through the trigger
    assert broker.position is None
    assert broker.pending_order is not None  # still resting for a pullback

    broker.on_bar(bar(2, 5009, 5012, 5008, 5010))  # trades back through at the limit
    assert broker.position is not None
    assert broker.position.entry_price == 5010.0


def test_entry_limit_must_sit_on_the_far_side_of_the_trigger():
    broker = SimulatedBroker(NO_COST, starting_equity=10_000.0)
    with pytest.raises(ValueError):
        broker.submit_bracket(Side.LONG, 1, 5010.0, 5000.0, 5020.0, T0, entry_limit=5009.0)


def test_take_profit_fills_when_only_the_target_is_touched():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))  # entry only
    broker.on_bar(bar(2, 5011, 5021, 5010, 5020))  # target only
    trade = broker.trades[0]
    assert trade.exit_reason is ExitReason.TAKE_PROFIT
    assert trade.exit_price == 5020.0
    assert trade.net_pnl == pytest.approx(50.0)  # 10 pts * 5 USD


def test_stop_is_assumed_first_when_a_bar_contains_both_levels():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    broker.on_bar(bar(2, 5011, 5025, 4995, 5020))  # touches target AND stop
    trade = broker.trades[0]
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.exit_price == 5000.0


def test_stop_gap_fills_at_the_open_below_the_stop():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    broker.on_bar(bar(2, 4990, 4992, 4985, 4988))
    trade = broker.trades[0]
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.exit_price == 4990.0
    assert trade.net_pnl == pytest.approx(-100.0)  # worse than the planned -50


def test_entry_and_stop_can_happen_inside_the_same_bar():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5015, 4995, 5001))
    assert broker.position is None
    assert broker.trades[0].exit_reason is ExitReason.STOP_LOSS


def test_short_bracket_mirrors_long_behaviour():
    broker = armed_broker(side=Side.SHORT)
    broker.on_bar(bar(1, 4995, 4996, 4988, 4989))  # entry at 4990
    assert broker.position.side is Side.SHORT
    broker.on_bar(bar(2, 4985, 4986, 4979, 4980))  # target 4980 touched
    trade = broker.trades[0]
    assert trade.exit_reason is ExitReason.TAKE_PROFIT
    assert trade.net_pnl == pytest.approx(50.0)


def test_slippage_and_commission_are_charged_on_both_sides():
    broker = SimulatedBroker(MES_FUTURE, starting_equity=10_000.0)
    broker.submit_bracket(Side.LONG, 1, 5010.0, 5000.0, 5020.0, T0)
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    # One tick of slippage on a stop entry.
    assert broker.position.entry_price == 5010.25
    broker.on_bar(bar(2, 5011, 5021, 5010, 5020))
    trade = broker.trades[0]
    assert trade.commission == pytest.approx(2 * MES_FUTURE.commission_per_unit)
    assert trade.net_pnl < 50.0


def test_slippage_is_recorded_so_spread_costs_can_be_reported():
    wide_spread = InstrumentSpec(
        symbol="CFD",
        tick_size=0.1,
        point_value=1.0,
        commission_per_unit=0.0,
        slippage_ticks=5.0,  # cost lives entirely in the spread
    )
    broker = SimulatedBroker(wide_spread, starting_equity=10_000.0)
    broker.submit_bracket(Side.LONG, 10, 5010.0, 5000.0, 5020.0, T0)
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    broker.on_bar(bar(2, 5011, 5011, 4990, 4995))  # stopped out
    trade = broker.trades[0]
    assert trade.entry_slippage_points == pytest.approx(0.5)
    assert trade.exit_slippage_points == pytest.approx(0.5)
    assert trade.commission == 0.0
    assert trade.friction == pytest.approx(10.0)  # 1.0 pt * 10 units * 1.0


def test_take_profit_exits_pay_no_slippage():
    broker = armed_broker(instrument=MES_FUTURE)
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    broker.on_bar(bar(2, 5011, 5021, 5010, 5020))
    trade = broker.trades[0]
    assert trade.entry_slippage_points == pytest.approx(MES_FUTURE.slippage_points)
    assert trade.exit_slippage_points == 0.0


def test_expired_order_is_removed_and_never_fills():
    broker = SimulatedBroker(NO_COST, starting_equity=10_000.0)
    broker.submit_bracket(
        Side.LONG, 1, 5010.0, 5000.0, 5020.0, T0, expires_at=T0 + timedelta(minutes=5)
    )
    broker.on_bar(bar(1, 5005, 5015, 5004, 5012))
    assert broker.position is None
    assert broker.pending_order is None


def test_close_position_flattens_at_the_last_close():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    trade = broker.close_position(ExitReason.SESSION_CLOSE, T0 + timedelta(minutes=10))
    assert trade.exit_reason is ExitReason.SESSION_CLOSE
    assert trade.exit_price == 5011.0
    assert broker.position is None


def test_equity_tracks_realised_pnl():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    broker.on_bar(bar(2, 5011, 5021, 5010, 5020))
    assert broker.equity == pytest.approx(10_050.0)
    assert broker.equity_curve[-1][1] == pytest.approx(10_050.0)


def test_bracket_validation_rejects_inverted_levels():
    broker = SimulatedBroker(NO_COST, starting_equity=10_000.0)
    with pytest.raises(ValueError):
        broker.submit_bracket(Side.LONG, 1, 5010.0, 5020.0, 5000.0, T0)
    with pytest.raises(ValueError):
        broker.submit_bracket(Side.LONG, 0, 5010.0, 5000.0, 5020.0, T0)


def test_cannot_arm_a_second_entry_while_in_a_position():
    broker = armed_broker()
    broker.on_bar(bar(1, 5005, 5012, 5004, 5011))
    with pytest.raises(RuntimeError):
        broker.submit_bracket(Side.LONG, 1, 5030.0, 5020.0, 5040.0, T0)
