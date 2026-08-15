"""
Tests for the first-candle range strategy (Nasdaq, 15m).

Setup under test: the opening candle defines a range, and the first candle to
CLOSE outside that range takes the trade — long above the high, short below the
low. A wick through the range is not a signal.
"""
from datetime import date, datetime, time, timedelta

import pytest

from src.config.trading_config import (
    BotConfig,
    FirstCandleBreakConfig,
    RiskConfig,
    SessionConfig,
)
from src.trading.broker import SimulatedBroker
from src.trading.engine import TradingBot
from src.trading.models import Bar, EntryType, ExitReason, InstrumentSpec, Side
from src.trading.risk import RiskManager
from src.trading.strategy import FirstCandleBreakStrategy

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


def make_strategy(**overrides) -> FirstCandleBreakStrategy:
    strategy = FirstCandleBreakStrategy(
        FirstCandleBreakConfig(**overrides), NAS_CLEAN, SESSION
    )
    strategy.on_session_start(DAY)
    return strategy


def feed(strategy, rows):
    signal = None
    for row in rows:
        signal = strategy.on_bar(bar(row))
    return signal


# ---------------------------------------------------------------------------
#  The range itself
# ---------------------------------------------------------------------------


def test_the_first_candle_defines_the_range_and_never_trades():
    strategy = make_strategy()
    assert strategy.on_bar(bar(OPENING_CANDLE)) is None
    assert strategy.range_high == 20080
    assert strategy.range_low == 19950


def test_session_start_clears_the_previous_day_range():
    strategy = make_strategy()
    feed(strategy, [OPENING_CANDLE])
    strategy.on_session_start(date(2026, 1, 6))
    assert strategy.range_high is None
    assert strategy.range_low is None
    assert not strategy.armed


def test_the_range_can_span_more_than_one_candle():
    strategy = make_strategy(range_minutes=30)
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20200, 19900, 20100)]
    assert feed(strategy, rows) is None  # both candles build the range
    assert strategy.range_high == 20200
    assert strategy.range_low == 19900


def test_the_range_is_measured_in_minutes_not_bars():
    """
    The same 15 minutes of the open must give the same range whatever the bar
    size — three 5m candles produce the range one 15m candle would.
    """
    strategy = make_strategy(range_minutes=15)
    five_minute_open = [
        (time(9, 30), 20000, 20050, 19950, 20020),
        (time(9, 35), 20020, 20080, 20000, 20050),
        (time(9, 40), 20050, 20060, 19980, 20050),
    ]
    assert feed(strategy, five_minute_open) is None  # all three build the range
    assert strategy.range_high == 20080  # same as the 15m OPENING_CANDLE
    assert strategy.range_low == 19950
    assert not strategy.armed  # 15 minutes have not elapsed until the next bar

    signal = strategy.on_bar(bar((time(9, 45), 20050, 20130, 20040, 20120)))
    assert signal is not None and signal.side is Side.LONG


# ---------------------------------------------------------------------------
#  Entry: the close is the trigger
# ---------------------------------------------------------------------------


def test_no_entry_while_closes_stay_inside_the_range():
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20070, 20000, 20040),
        (time(10, 0), 20040, 20060, 20010, 20030),
    ]
    assert feed(strategy, rows) is None


def test_a_wick_through_the_range_is_not_a_signal():
    """The distinction from a stop-order breakout: the CLOSE has to hold."""
    strategy = make_strategy()
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20150, 20040, 20070),  # spikes above, closes inside
        (time(10, 0), 20070, 20075, 19900, 20000),  # spikes below, closes inside
    ]
    assert feed(strategy, rows) is None


def test_long_on_the_first_close_above_the_range():
    strategy = make_strategy()
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    signal = feed(strategy, rows)
    assert signal is not None
    assert signal.side is Side.LONG
    assert signal.entry_type is EntryType.MARKET
    assert signal.entry_stop is None  # market order, nothing resting
    assert signal.reference_price == 20120
    assert signal.stop_loss == 19949.5  # range low minus a 2-tick buffer
    assert signal.risk_points == pytest.approx(170.5)


def test_short_on_the_first_close_below_the_range():
    strategy = make_strategy()
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20060, 19900, 19920)]
    signal = feed(strategy, rows)
    assert signal.side is Side.SHORT
    assert signal.stop_loss == 20080.5  # range high plus the buffer
    assert signal.risk_points == pytest.approx(160.5)


def test_a_close_exactly_on_the_range_edge_is_not_outside_it():
    strategy = make_strategy()
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20090, 20040, 20080)]
    assert feed(strategy, rows) is None


def test_the_stop_sits_beyond_the_range_never_inside_it():
    strategy = make_strategy(stop_buffer_ticks=0.0)
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    signal = feed(strategy, rows)
    assert signal.stop_loss == 19950  # exactly the range low, no buffer
    assert signal.stop_loss <= strategy.range_low


def test_target_is_one_to_one_by_construction():
    strategy = make_strategy()
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    signal = feed(strategy, rows)
    assert signal.reward_risk_ratio == 1.0
    assert signal.reward_points == pytest.approx(signal.risk_points)


# ---------------------------------------------------------------------------
#  Filters and limits
# ---------------------------------------------------------------------------


def test_wide_opening_candles_are_skipped():
    strategy = make_strategy(max_range_points=100.0)  # this range is 130
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    assert feed(strategy, rows) is None


def test_narrow_opening_candles_are_skipped():
    strategy = make_strategy(min_range_points=200.0)
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    assert feed(strategy, rows) is None


def test_disabled_direction_is_not_traded():
    strategy = make_strategy(allow_long=False)
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    assert feed(strategy, rows) is None


def test_one_entry_per_session_by_default():
    strategy = make_strategy()
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    assert feed(strategy, rows) is not None
    strategy.on_entry_filled(position=None)
    assert strategy.on_bar(bar((time(10, 0), 20120, 20200, 20110, 20180))) is None


# ---------------------------------------------------------------------------
#  Optional variant: wait for the failed move
# ---------------------------------------------------------------------------


def test_excursion_variant_ignores_the_first_close_outside():
    strategy = make_strategy(require_excursion=True)
    rows = [OPENING_CANDLE, (time(9, 45), 20050, 20130, 20040, 20120)]
    assert feed(strategy, rows) is None


def test_excursion_variant_enters_after_price_returns_and_breaks_again():
    strategy = make_strategy(require_excursion=True)
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),   # sale del rango
        (time(10, 0), 20120, 20125, 20000, 20020),   # vuelve dentro
        (time(10, 15), 20020, 20110, 20015, 20100),  # cierra fuera otra vez
    ]
    signal = feed(strategy, rows)
    assert signal is not None
    assert signal.side is Side.LONG


def test_excursion_variant_flips_direction_when_the_break_fails():
    strategy = make_strategy(require_excursion=True)
    rows = [
        OPENING_CANDLE,
        (time(9, 45), 20050, 20130, 20040, 20120),   # rompe al alza
        (time(10, 0), 20120, 20125, 20000, 20020),   # vuelve dentro
        (time(10, 15), 20020, 20030, 19900, 19920),  # cierra por debajo
    ]
    assert feed(strategy, rows).side is Side.SHORT


# ---------------------------------------------------------------------------
#  End to end: the bot actually takes the trade
# ---------------------------------------------------------------------------


def day_bars_15m(rows, day=DAY, filler=20120.0) -> list[Bar]:
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


def first_candle_bot(instrument=NAS_CLEAN, equity=100_000.0) -> TradingBot:
    config = BotConfig(
        instrument=instrument,
        session=SESSION,
        risk=RiskConfig(risk_per_trade_pct=0.5, max_trades_per_day=1),
        strategy=FirstCandleBreakConfig(),
        starting_equity=equity,
        timeframe_minutes=15,
    )
    broker = SimulatedBroker(instrument, equity)
    strategy = FirstCandleBreakStrategy(config.strategy, instrument, SESSION)
    risk = RiskManager(config.risk, instrument)
    return TradingBot(config, strategy, broker, risk)


BREAK_DAY = [
    OPENING_CANDLE,
    (time(9, 45), 20050, 20130, 20040, 20120),  # closes above -> signal
    (time(10, 0), 20122, 20140, 20115, 20130),  # entry happens on this open
]


def test_market_entry_fills_at_the_open_after_the_confirming_close():
    bot = first_candle_bot()
    bot.run(day_bars_15m(BREAK_DAY))
    assert bot.broker.trades, "expected the break to be traded"
    trade = bot.broker.trades[0]
    assert trade.side is Side.LONG
    assert trade.entry_time.time() == time(10, 0)
    assert trade.entry_price == 20122  # the 10:00 open, not the 09:45 close


def test_target_is_measured_from_the_actual_fill():
    bot = first_candle_bot()
    bot.run(day_bars_15m(BREAK_DAY))
    trade = bot.broker.trades[0]
    risk = trade.entry_price - 19949.5  # fill to the structural stop
    assert trade.planned_risk_points == pytest.approx(risk)
    if trade.exit_reason is ExitReason.TAKE_PROFIT:
        assert trade.exit_price - trade.entry_price == pytest.approx(risk, abs=0.25)


def test_the_real_risk_never_exceeds_the_budget():
    """
    Size is estimated from the confirming close but the fill arrives later and
    higher, which widens the real stop. The cap has to hold anyway.
    """
    bot = first_candle_bot(equity=100_000.0)
    bot.run(day_bars_15m(BREAK_DAY))
    trade = bot.broker.trades[0]
    risked = trade.planned_risk_points * trade.qty * trade.point_value
    assert risked <= 500.0  # 0.5% of 100k
    assert trade.qty == pytest.approx(2.8, abs=0.05)


def test_no_position_is_carried_overnight():
    bot = first_candle_bot()
    bot.run(day_bars_15m(BREAK_DAY))
    trade = bot.broker.trades[0]
    assert trade.entry_time.date() == trade.exit_time.date()
    assert bot.broker.position is None


def test_every_target_hit_pays_exactly_one_r_in_price_terms():
    """
    The property the whole strategy rests on: reward distance equals risk
    distance on every winner, measured from the real fill, whatever the open
    gave us. Costs are separate — they come out of the money, not the levels.
    """
    from src.trading.data import synthetic_bars

    bars = synthetic_bars(
        days=120, minutes=15, start_price=20_000.0, bar_volatility_points=18.0,
        gap_volatility_points=45.0, trend_points_per_day=6.0, seed=21, tick_size=0.25,
    )
    bot = first_candle_bot(equity=250_000.0)
    bot.run([b for b in bars if time(9, 30) <= b.timestamp.time() < time(16, 0)])

    winners = [t for t in bot.broker.trades if t.exit_reason is ExitReason.TAKE_PROFIT]
    assert len(winners) >= 10, "expected a meaningful number of target hits"
    for trade in winners:
        risk = abs(trade.entry_price - 0) and abs(trade.entry_price - trade.exit_price)
        planned = trade.planned_risk_points
        # Reward distance == planned risk distance, within one tick of rounding.
        assert risk == pytest.approx(planned, abs=0.25), (
            f"{trade.entry_time}: reward {risk} vs risk {planned}"
        )
