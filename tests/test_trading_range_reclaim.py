"""
Tests for the first-candle range reclaim strategy (Nasdaq, 15m).

Setup under test: the opening candle defines a range, price closes outside it,
closes back inside, and the next close outside is the entry — long above,
short below, whichever way that close goes.
"""
from datetime import date, datetime, time, timedelta

import pytest

from src.config.trading_config import (
    NAS100_CFD,
    BotConfig,
    RangeReclaimConfig,
    RiskConfig,
    SessionConfig,
)
from src.trading.backtest import build_bot
from src.trading.broker import SimulatedBroker
from src.trading.engine import TradingBot
from src.trading.models import Bar, EntryType, ExitReason, InstrumentSpec, Side
from src.trading.risk import RiskManager
from src.trading.strategy import RangeReclaimStrategy

DAY = date(2026, 1, 5)
SESSION = SessionConfig(opening_range_minutes=15, flat_at=time(15, 45))

# Zero-cost Nasdaq CFD keeps the arithmetic in the tests exact.
NAS_CLEAN = InstrumentSpec(
    symbol="NAS100",
    tick_size=0.25,
    point_value=1.0,
    qty_step=0.1,
    min_qty=0.1,
    commission_per_unit=0.0,
    slippage_ticks=0.0,
)

# First candle: range 19950 - 20080 (width 130).
OPENING_CANDLE = (time(9, 30), 20000, 20080, 19950, 20050)


def bar(row) -> Bar:
    t, o, h, l, c = row
    return Bar(datetime.combine(DAY, t), o, h, l, c)


def make_strategy(**overrides) -> RangeReclaimStrategy:
    config = RangeReclaimConfig(**overrides)
    strategy = RangeReclaimStrategy(config, NAS_CLEAN, SESSION)
    strategy.on_session_start(DAY)
    return strategy


def feed(strategy, rows):
    signal = None
    for row in rows:
        signal = strategy.on_bar(bar(row))
    return signal


def test_the_first_candle_defines_the_range_and_never_trades():
    strategy = make_strategy()
    assert strategy.on_bar(bar(OPENING_CANDLE)) is None
    assert strategy.range_high == 20080
    assert strategy.range_low == 19950


def test_no_entry_while_price_stays_inside_the_range():
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20070, 20000, 20040),
        (time(10, 0), 20040, 20060, 20010, 20030),
    ]
    assert feed(strategy, rows) is None


def test_no_entry_while_price_leaves_and_never_comes_back():
    """The setup needs the failed move, not just a breakout."""
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),  # closes above
        (time(10, 0), 20120, 20200, 20110, 20180),  # keeps closing above
        (time(10, 15), 20180, 20250, 20170, 20240),
    ]
    assert feed(strategy, rows) is None


def test_long_entry_after_the_range_is_reclaimed():
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),  # sale del rango
        (time(10, 0), 20120, 20125, 20000, 20020),  # vuelve dentro
        (time(10, 15), 20020, 20110, 20015, 20100),  # cierra fuera otra vez
    ]
    signal = feed(strategy, rows)
    assert signal is not None
    assert signal.side is Side.LONG
    assert signal.entry_type is EntryType.MARKET
    assert signal.entry_stop is None  # market order, no resting level
    assert signal.reference_price == 20100
    assert signal.stop_loss == 19949.5  # range low minus a 2-tick buffer
    assert signal.risk_points == pytest.approx(150.5)


def test_short_entry_when_the_break_fails_the_other_way():
    """'O al revés': breaks up, comes back, and closes below the low instead."""
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),  # rompe al alza
        (time(10, 0), 20120, 20125, 20000, 20020),  # vuelve dentro
        (time(10, 15), 20020, 20030, 19900, 19920),  # cierra por debajo
    ]
    signal = feed(strategy, rows)
    assert signal.side is Side.SHORT
    assert signal.stop_loss == 20080.5  # range high plus the buffer
    assert signal.risk_points == pytest.approx(160.5)


def test_the_stop_sits_beyond_the_range_never_inside_it():
    strategy = make_strategy(stop_buffer_ticks=0.0)
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),
        (time(10, 0), 20120, 20125, 20000, 20020),
        (time(10, 15), 20020, 20110, 20015, 20100),
    ]
    signal = feed(strategy, rows)
    assert signal.stop_loss == 19950  # exactly the range low with no buffer
    assert signal.stop_loss <= strategy.range_low


def test_excursion_requirement_can_be_disabled():
    strategy = make_strategy(require_excursion=False)
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),  # first close outside
    ]
    signal = feed(strategy, rows)
    assert signal is not None
    assert signal.side is Side.LONG


def test_wide_opening_candles_are_skipped():
    strategy = make_strategy(max_range_points=100.0)  # this range is 130
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),
        (time(10, 0), 20120, 20125, 20000, 20020),
        (time(10, 15), 20020, 20110, 20015, 20100),
    ]
    assert feed(strategy, rows) is None


def test_narrow_opening_candles_are_skipped():
    strategy = make_strategy(min_range_points=200.0)
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),
        (time(10, 0), 20120, 20125, 20000, 20020),
        (time(10, 15), 20020, 20110, 20015, 20100),
    ]
    assert feed(strategy, rows) is None


def test_disabled_direction_is_not_traded():
    strategy = make_strategy(allow_long=False)
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),
        (time(10, 0), 20120, 20125, 20000, 20020),
        (time(10, 15), 20020, 20110, 20015, 20100),
    ]
    assert feed(strategy, rows) is None


def test_one_entry_per_session_by_default():
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),
        (time(10, 0), 20120, 20125, 20000, 20020),
        (time(10, 15), 20020, 20110, 20015, 20100),
    ]
    assert feed(strategy, rows) is not None
    strategy.on_entry_filled(position=None)
    assert strategy.on_bar(bar((time(10, 30), 20100, 20150, 20090, 20140))) is None


def test_session_start_clears_the_previous_day_range():
    strategy = make_strategy()
    feed(strategy, [OPENING_CANDLE])
    strategy.on_session_start(date(2026, 1, 6))
    assert strategy.range_high is None
    assert strategy.range_low is None
    assert not strategy.armed


# ---------------------------------------------------------------------------
#  End to end: the bot actually takes the trade
# ---------------------------------------------------------------------------


def day_bars_15m(rows, day=DAY, filler=20050.0) -> list[Bar]:
    explicit = {t: (o, h, l, c) for t, o, h, l, c in rows}
    bars = []
    ts = datetime.combine(day, time(9, 30))
    end = datetime.combine(day, time(16, 0))
    while ts < end:
        if ts.time() in explicit:
            o, h, l, c = explicit[ts.time()]
            bars.append(Bar(ts, o, h, l, c))
        else:
            bars.append(Bar(ts, filler, filler + 2, filler - 2, filler))
        ts += timedelta(minutes=15)
    return bars


def reclaim_bot(instrument=NAS_CLEAN, equity=100_000.0) -> TradingBot:
    config = BotConfig(
        instrument=instrument,
        session=SESSION,
        risk=RiskConfig(risk_per_trade_pct=0.5, max_trades_per_day=1),
        strategy=None,  # replaced below
        starting_equity=equity,
        timeframe_minutes=15,
    )
    broker = SimulatedBroker(instrument, equity)
    strategy = RangeReclaimStrategy(RangeReclaimConfig(), instrument, SESSION)
    risk = RiskManager(config.risk, instrument)
    return TradingBot(config, strategy, broker, risk)


RECLAIM_DAY = [
    OPENING_CANDLE,
    (time(9, 45), 20050, 20130, 20040, 20120),   # sale
    (time(10, 0), 20120, 20125, 20000, 20020),   # vuelve
    (time(10, 15), 20020, 20110, 20015, 20100),  # confirma -> señal
    (time(10, 30), 20102, 20140, 20095, 20130),  # aquí entra, en la apertura
]


def test_market_entry_fills_at_the_open_after_the_confirming_close():
    bot = reclaim_bot()
    bot.run(day_bars_15m(RECLAIM_DAY))
    position_trades = bot.broker.trades
    assert position_trades, "expected the reclaim to be traded"
    trade = position_trades[0]
    assert trade.side is Side.LONG
    assert trade.entry_time.time() == time(10, 30)
    assert trade.entry_price == 20102  # the 10:30 open, not the 10:15 close


def test_target_is_measured_from_the_actual_fill_so_the_ratio_stays_one_to_one():
    bot = reclaim_bot()
    bot.run(day_bars_15m(RECLAIM_DAY))
    trade = bot.broker.trades[0]
    risk = trade.entry_price - 19949.5   # fill to structural stop
    if trade.exit_reason is ExitReason.TAKE_PROFIT:
        reward = trade.exit_price - trade.entry_price
        assert reward == pytest.approx(risk, abs=0.25)
    assert trade.planned_risk_points == pytest.approx(risk)


def test_position_is_sized_from_the_structural_stop():
    bot = reclaim_bot(equity=100_000.0)
    bot.run(day_bars_15m(RECLAIM_DAY))
    trade = bot.broker.trades[0]
    # 0.5% of 100k = 500 budget; ~152.5 points of risk at 1 USD per point.
    assert trade.qty == pytest.approx(3.2, abs=0.1)
    risked = trade.planned_risk_points * trade.qty * trade.point_value
    assert risked <= 500.0
