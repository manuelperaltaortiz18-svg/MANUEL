"""End-to-end tests for the bot loop: session rules, risk gates, no overnight risk."""
from datetime import date, datetime, time, timedelta

import pytest

from src.config.trading_config import (
    MES_FUTURE,
    BotConfig,
    BreakoutConfig,
    RiskConfig,
    SessionConfig,
)
from src.trading.backtest import build_bot, run_backtest
from src.trading.data import synthetic_bars
from src.trading.models import Bar, ExitReason, Side

DAY = date(2026, 1, 5)
SESSION = SessionConfig(opening_range_minutes=15)

# Opening range 4995-5012 -> long entry 5012.25, stop 4995.25, target 5029.25.
OPENING_RANGE_ROWS = [
    (time(9, 30), 5000, 5010, 4995, 5005),
    (time(9, 35), 5005, 5012, 5000, 5008),
    (time(9, 40), 5008, 5011, 5002, 5009),
    (time(9, 45), 5009, 5010, 5005, 5009),
]
BREAKOUT_ROW = (time(9, 50), 5009, 5020, 5008, 5018)


def make_config(**risk_overrides) -> BotConfig:
    return BotConfig(
        instrument=MES_FUTURE,
        session=SESSION,
        risk=RiskConfig(**risk_overrides),
        strategy=BreakoutConfig(mode="opening_range", stop_mode="range", atr_period=3),
        starting_equity=25_000.0,
    )


def day_bars(rows, day=DAY, filler=5009.0) -> list[Bar]:
    """A full 09:30-16:00 session: explicit rows plus quiet filler bars."""
    explicit = {t: (o, h, l, c) for t, o, h, l, c in rows}
    bars = []
    ts = datetime.combine(day, time(9, 30))
    end = datetime.combine(day, time(16, 0))
    while ts < end:
        if ts.time() in explicit:
            o, h, l, c = explicit[ts.time()]
            bars.append(Bar(ts, o, h, l, c))
        else:
            bars.append(Bar(ts, filler, filler + 0.5, filler - 0.5, filler))
        ts += timedelta(minutes=5)
    return bars


def run(rows, config=None, day=DAY):
    config = config or make_config()
    bot = build_bot(config)
    bot.run(day_bars(rows, day=day))
    return bot


def test_breakout_is_taken_and_target_pays_one_r():
    bot = run(OPENING_RANGE_ROWS + [BREAKOUT_ROW, (time(9, 55), 5018, 5032, 5017, 5030)])
    trades = bot.broker.trades
    assert len(trades) == 1
    trade = trades[0]
    assert trade.side is Side.LONG
    assert trade.entry_price == 5012.50  # 5012.25 level + 1 tick of slippage
    assert trade.exit_reason is ExitReason.TAKE_PROFIT
    assert trade.exit_price == 5029.25
    assert trade.r_multiple == pytest.approx(1.0, abs=0.1)


def test_stop_out_costs_about_one_r():
    bot = run(OPENING_RANGE_ROWS + [BREAKOUT_ROW, (time(9, 55), 5018, 5019, 4994, 4996)])
    trade = bot.broker.trades[0]
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.r_multiple == pytest.approx(-1.0, abs=0.1)


def test_open_position_is_flattened_at_the_session_flat_time():
    bot = run(OPENING_RANGE_ROWS + [BREAKOUT_ROW])
    trades = bot.broker.trades
    assert len(trades) == 1
    assert trades[0].exit_reason is ExitReason.SESSION_CLOSE
    assert trades[0].exit_time.time() == SESSION.flat_at
    assert bot.broker.position is None


def test_no_resting_order_survives_the_entry_cutoff():
    bot = build_bot(make_config())
    for bar in day_bars(OPENING_RANGE_ROWS):
        bot.on_bar(bar)
        if bar.timestamp.time() >= SESSION.entry_cutoff:
            assert bot.broker.pending_order is None
    assert bot.broker.pending_order is None


def test_order_rests_between_the_signal_and_the_cutoff():
    bot = build_bot(make_config())
    armed = False
    for bar in day_bars(OPENING_RANGE_ROWS):
        bot.on_bar(bar)
        if bar.timestamp.time() == time(9, 45):
            armed = bot.broker.pending_order is not None
    assert armed


def test_daily_trade_cap_is_enforced_by_the_bot():
    rows = OPENING_RANGE_ROWS + [
        BREAKOUT_ROW,
        (time(9, 55), 5018, 5032, 5017, 5030),  # target
        (time(10, 30), 5009, 5020, 5008, 5018),  # second breakout
        (time(10, 35), 5018, 5032, 5017, 5030),  # second target
        (time(11, 30), 5009, 5020, 5008, 5018),  # third breakout attempt
    ]
    bot = run(rows, config=make_config(max_trades_per_day=1))
    assert len(bot.broker.trades) == 1
    assert any("daily trade cap" in reason for _, reason in bot.rejected_signals)


def test_signals_are_rejected_when_size_rounds_to_zero():
    config = BotConfig(
        instrument=MES_FUTURE,
        session=SESSION,
        risk=RiskConfig(risk_per_trade_pct=0.1),  # 1 USD budget on 1k equity
        strategy=BreakoutConfig(mode="opening_range", stop_mode="range", atr_period=3),
        starting_equity=1_000.0,
    )
    bot = run(OPENING_RANGE_ROWS + [BREAKOUT_ROW], config=config)
    assert bot.broker.trades == []
    assert any("size 0" in reason for _, reason in bot.rejected_signals)


def test_multi_day_backtest_never_carries_risk_overnight():
    bars = synthetic_bars(days=25, minutes=5, seed=7)
    config = BotConfig(
        instrument=MES_FUTURE,
        session=SESSION,
        risk=RiskConfig(),
        strategy=BreakoutConfig(mode="opening_range", stop_mode="atr", atr_period=14),
        starting_equity=25_000.0,
    )
    result = run_backtest(bars, config)
    assert result.trades, "synthetic data should produce trades"
    for trade in result.trades:
        assert trade.entry_time.date() == trade.exit_time.date()
        assert trade.exit_time.time() <= SESSION.flat_at
    assert result.report.trades == len(result.trades)
    assert result.equity_curve[0] == config.starting_equity


def test_take_profit_trades_realise_close_to_plus_one_r():
    bars = synthetic_bars(days=40, minutes=5, seed=11)
    result = run_backtest(bars, make_config())
    winners = [t for t in result.trades if t.exit_reason is ExitReason.TAKE_PROFIT]
    assert winners, "expected at least one target hit"
    for trade in winners:
        # Never above +1R: entry slippage and both commissions are already
        # deducted. On tight stops that drag is large, which is exactly why the
        # required hit rate sits well above 50%.
        assert 0.5 <= trade.r_multiple <= 1.0


def test_bot_holds_at_most_one_position_at_a_time():
    bars = synthetic_bars(days=15, minutes=5, seed=3)
    bot = build_bot(make_config())
    for bar in bars:
        bot.on_bar(bar)
        assert bot.broker.position is None or bot.broker.pending_order is None
    bot.finish()
