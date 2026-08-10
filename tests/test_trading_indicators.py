"""Tests for the indicator layer."""
from datetime import datetime, timedelta

import pytest

from src.trading.indicators import (
    RollingExtremes,
    WilderATR,
    atr,
    ema,
    highest_high,
    lowest_low,
    sma,
    true_range,
)
from src.trading.models import Bar


def make_bars(rows):
    start = datetime(2026, 1, 5, 9, 30)
    return [
        Bar(start + timedelta(minutes=5 * i), o, h, l, c)
        for i, (o, h, l, c) in enumerate(rows)
    ]


def test_sma_and_ema_need_a_full_window():
    assert sma([1, 2], 3) is None
    assert sma([1, 2, 3, 4], 3) == pytest.approx(3.0)
    assert ema([1, 2], 3) is None
    # Seeded with the SMA of the first 3 values (2.0), then smoothed by k=0.5.
    assert ema([1, 2, 3, 4], 3) == pytest.approx(3.0)


def test_true_range_uses_previous_close_gaps():
    bar = Bar(datetime(2026, 1, 5, 9, 30), open=105, high=106, low=104, close=105)
    assert true_range(bar, None) == 2
    assert true_range(bar, prev_close=100) == 6  # gap up from 100 to a 106 high


def test_atr_matches_manual_wilder_calculation():
    bars = make_bars([(100, 102, 100, 101), (101, 103, 101, 102), (102, 104, 102, 103)])
    # TRs: 2, 2, 2 -> seed average is 2.0
    assert atr(bars, 3) == pytest.approx(2.0)
    assert atr(bars[:2], 3) is None


def test_wilder_atr_smooths_after_seeding():
    bars = make_bars([(100, 102, 100, 101), (101, 103, 101, 102), (102, 104, 102, 103)])
    tracker = WilderATR(2)
    assert tracker.update(bars[0]) is None
    seeded = tracker.update(bars[1])
    assert seeded == pytest.approx(2.0)
    # New TR of 2 keeps the average at 2.0.
    assert tracker.update(bars[2]) == pytest.approx(2.0)


def test_highest_and_lowest_with_offset():
    bars = make_bars([(100, 105, 99, 104), (104, 110, 103, 108), (108, 109, 101, 102)])
    assert highest_high(bars, 3) == 110
    assert lowest_low(bars, 3) == 99
    # Excluding the most recent bar.
    assert highest_high(bars, 2, offset=1) == 110
    assert lowest_low(bars, 1, offset=2) == 99
    assert highest_high(bars, 5) is None


def test_rolling_extremes_window_rolls_off():
    bars = make_bars([(100, 105, 99, 104), (104, 110, 103, 108), (108, 109, 101, 102)])
    roll = RollingExtremes(2)
    roll.update(bars[0])
    assert not roll.is_ready
    roll.update(bars[1])
    assert roll.is_ready
    assert roll.highest == 110
    roll.update(bars[2])
    assert roll.highest == 110
    assert roll.lowest == 101  # the first bar has dropped out of the window
