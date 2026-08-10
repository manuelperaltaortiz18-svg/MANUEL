"""Tests for the breakout strategy, above all the 1:1 invariant."""
from datetime import date, datetime, time, timedelta

import pytest

from src.config.trading_config import MES_FUTURE, BreakoutConfig, SessionConfig
from src.trading.models import Bar, Side
from src.trading.strategy import BreakoutStrategy

SESSION = SessionConfig(opening_range_minutes=15)
DAY = date(2026, 1, 5)

# Opening range: high 5012, low 4995 (width 17) built from the 09:30-09:45 bars.
OPENING_RANGE_BARS = [
    (time(9, 30), 5000, 5010, 4995, 5005),
    (time(9, 35), 5005, 5012, 5000, 5008),
    (time(9, 40), 5008, 5011, 5002, 5009),
]


def bar(t: time, o, h, l, c) -> Bar:
    return Bar(datetime.combine(DAY, t), o, h, l, c)


def make_strategy(**overrides) -> BreakoutStrategy:
    config = BreakoutConfig(
        mode="opening_range",
        stop_mode="range",
        range_multiple=1.0,
        atr_period=3,
        **overrides,
    )
    strategy = BreakoutStrategy(config, MES_FUTURE, SESSION)
    strategy.on_session_start(DAY)
    return strategy


def feed(strategy, rows):
    signal = None
    for row in rows:
        signal = strategy.on_bar(bar(*row))
    return signal


def test_no_signal_while_the_opening_range_is_still_forming():
    strategy = make_strategy()
    assert feed(strategy, OPENING_RANGE_BARS) is None


def test_signal_bracket_is_exactly_one_to_one():
    strategy = make_strategy()
    signal = feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal is not None
    assert signal.risk_points == pytest.approx(signal.reward_points)
    assert signal.reward_risk_ratio == pytest.approx(1.0)


def test_long_breakout_levels_sit_one_tick_above_the_range():
    strategy = make_strategy()
    signal = feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal.side is Side.LONG
    assert signal.entry_stop == 5012.25  # range high 5012 + 1 tick
    assert signal.stop_loss == 4995.25  # 17-point range width
    assert signal.take_profit == 5029.25


def test_short_is_armed_when_price_leans_below_the_midpoint():
    strategy = make_strategy()
    signal = feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5000, 5001, 4996, 4997)])
    assert signal.side is Side.SHORT
    assert signal.entry_stop == 4994.75  # range low 4995 - 1 tick
    assert signal.stop_loss == 5011.75
    assert signal.risk_points == pytest.approx(signal.reward_points)


def test_stop_distance_is_clamped_to_the_configured_bounds():
    tight = make_strategy(max_stop_points=5.0)
    signal = feed(tight, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal.risk_points == pytest.approx(5.0)

    wide = make_strategy(min_stop_points=25.0)
    signal = feed(wide, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal.risk_points == pytest.approx(25.0)


def test_reward_risk_ratio_is_configurable_but_defaults_to_one():
    strategy = make_strategy(reward_risk_ratio=2.0)
    signal = feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal.reward_risk_ratio == pytest.approx(2.0)
    assert BreakoutConfig().reward_risk_ratio == 1.0


def test_atr_stop_mode_waits_for_the_atr_to_be_ready():
    config = BreakoutConfig(mode="opening_range", stop_mode="atr", atr_period=20)
    strategy = BreakoutStrategy(config, MES_FUTURE, SESSION)
    strategy.on_session_start(DAY)
    assert feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)]) is None


def test_atr_stop_mode_sizes_the_stop_from_volatility():
    config = BreakoutConfig(
        mode="opening_range", stop_mode="atr", atr_period=3, atr_multiple=1.0
    )
    strategy = BreakoutStrategy(config, MES_FUTURE, SESSION)
    strategy.on_session_start(DAY)
    signal = feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal is not None
    assert signal.risk_points == pytest.approx(signal.meta["stop_distance"])
    assert signal.meta["atr"] > 0


def test_narrow_ranges_are_skipped():
    strategy = make_strategy(min_range_points=50.0)
    assert feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)]) is None


def test_daily_signal_cap_stops_further_proposals():
    strategy = make_strategy(max_signals_per_day=1)
    rows = OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)]
    assert feed(strategy, rows) is not None
    strategy.on_entry_filled(position=None)
    assert strategy.on_bar(bar(time(9, 50), 5009, 5010, 5005, 5009)) is None


def test_session_start_resets_the_daily_counters():
    strategy = make_strategy(max_signals_per_day=1)
    feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    strategy.on_entry_filled(position=None)
    strategy.on_session_start(date(2026, 1, 6))
    assert feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)]) is not None


def test_disabled_direction_is_never_proposed():
    downtrend = [
        (time(9, 30), 5010, 5012, 5000, 5002),
        (time(9, 35), 5002, 5004, 4990, 4992),
        (time(9, 40), 4992, 4994, 4980, 4982),
        (time(9, 45), 4982, 4984, 4975, 4978),
    ]
    strategy = make_strategy(trend_filter_period=3, allow_short=False)
    assert feed(strategy, downtrend) is None

    with_shorts = make_strategy(trend_filter_period=3)
    assert feed(with_shorts, downtrend).side is Side.SHORT


def test_donchian_mode_waits_for_the_full_lookback():
    config = BreakoutConfig(
        mode="donchian", lookback_bars=4, stop_mode="range", atr_period=3
    )
    strategy = BreakoutStrategy(config, MES_FUTURE, SESSION)
    strategy.on_session_start(DAY)
    rows = [
        (time(9, 30), 5000, 5010, 4995, 5005),
        (time(9, 35), 5005, 5012, 5000, 5008),
        (time(9, 40), 5008, 5011, 5002, 5009),
    ]
    assert feed(strategy, rows) is None
    signal = strategy.on_bar(bar(time(9, 45), 5009, 5013, 5005, 5012))
    assert signal is not None
    assert signal.entry_stop == 5013.25  # highest high of the last 4 bars + 1 tick


def test_signal_expires_at_the_session_flat_time():
    strategy = make_strategy()
    signal = feed(strategy, OPENING_RANGE_BARS + [(time(9, 45), 5009, 5010, 5005, 5009)])
    assert signal.valid_until == datetime.combine(DAY, SESSION.flat_at)
