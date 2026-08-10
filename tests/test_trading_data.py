"""Tests for CSV loading, resampling, session filtering and the synthetic feed."""
from datetime import date, datetime, time, timedelta

import pytest

from src.trading.data import (
    filter_session,
    group_by_day,
    load_csv,
    parse_timestamp,
    resample,
    synthetic_bars,
)
from src.trading.models import Bar

CSV = """timestamp,open,high,low,close,volume
2026-01-05T09:30:00,5000.00,5005.00,4998.00,5003.00,1200
2026-01-05T09:31:00,5003.00,5008.00,5002.00,5007.00,900
2026-01-05T09:32:00,5007.00,5009.00,5001.00,5002.00,1100
"""


def test_parse_timestamp_accepts_common_vendor_formats():
    assert parse_timestamp("2026-01-05T09:30:00") == datetime(2026, 1, 5, 9, 30)
    assert parse_timestamp("2026-01-05 09:30") == datetime(2026, 1, 5, 9, 30)
    assert parse_timestamp("05/01/2026 09:30:00") == datetime(2026, 1, 5, 9, 30)
    with pytest.raises(ValueError):
        parse_timestamp("not a date")


def test_load_csv_reads_bars_in_order(tmp_path):
    path = tmp_path / "bars.csv"
    path.write_text(CSV, encoding="utf-8")
    bars = load_csv(path)
    assert len(bars) == 3
    assert bars[0].timestamp == datetime(2026, 1, 5, 9, 30)
    assert bars[-1].close == 5002.00
    assert bars[0].volume == 1200


def test_load_csv_rejects_files_without_a_timestamp_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("open,high,low,close\n1,2,0,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_csv(path)


def test_resample_aggregates_ohlcv_correctly(tmp_path):
    path = tmp_path / "bars.csv"
    path.write_text(CSV, encoding="utf-8")
    bars = resample(load_csv(path), 5)
    assert len(bars) == 1
    candle = bars[0]
    assert candle.timestamp == datetime(2026, 1, 5, 9, 30)
    assert candle.open == 5000.00
    assert candle.high == 5009.00
    assert candle.low == 4998.00
    assert candle.close == 5002.00
    assert candle.volume == 3200


def test_resample_buckets_are_anchored_to_the_hour():
    start = datetime(2026, 1, 5, 9, 33)
    bars = [
        Bar(start + timedelta(minutes=i), 100 + i, 101 + i, 99 + i, 100 + i)
        for i in range(10)
    ]
    out = resample(bars, 5)
    assert [b.timestamp.minute for b in out] == [30, 35, 40]


def test_filter_session_keeps_only_rth_weekday_bars():
    bars = [
        Bar(datetime(2026, 1, 5, 9, 0), 100, 101, 99, 100),  # pre-market Monday
        Bar(datetime(2026, 1, 5, 10, 0), 100, 101, 99, 100),  # in session
        Bar(datetime(2026, 1, 5, 16, 0), 100, 101, 99, 100),  # at the close
        Bar(datetime(2026, 1, 10, 10, 0), 100, 101, 99, 100),  # Saturday
    ]
    kept = filter_session(bars, time(9, 30), time(16, 0))
    assert len(kept) == 1
    assert kept[0].timestamp.hour == 10


def test_group_by_day():
    bars = synthetic_bars(days=3, minutes=30)
    days = group_by_day(bars)
    assert len(days) == 3
    assert all(bars_of_day for bars_of_day in days.values())


def test_synthetic_feed_is_deterministic_and_skips_weekends():
    a = synthetic_bars(days=5, minutes=30, seed=1)
    b = synthetic_bars(days=5, minutes=30, seed=1)
    c = synthetic_bars(days=5, minutes=30, seed=2)
    assert [bar.close for bar in a] == [bar.close for bar in b]
    assert [bar.close for bar in a] != [bar.close for bar in c]
    assert all(bar.timestamp.weekday() < 5 for bar in a)


def test_synthetic_feed_respects_the_session_window():
    bars = synthetic_bars(
        days=2, minutes=15, session_start=time(9, 30), session_end=time(11, 0)
    )
    assert len(bars) == 2 * 6
    assert bars[0].timestamp.time() == time(9, 30)
    assert bars[5].timestamp.time() == time(10, 45)
    assert bars[0].timestamp.date() == date(2026, 1, 5)
