"""
Market data plumbing: CSV loading, timeframe resampling, session filtering and
a deterministic synthetic feed so the bot can be exercised without a data
provider.

Expected CSV layout (header required, extra columns ignored):

    timestamp,open,high,low,close,volume
    2026-01-02T09:30:00,4780.25,4783.50,4779.00,4782.75,15230
"""
from __future__ import annotations

import csv
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

from src.trading.models import Bar

_TIMESTAMP_FIELDS = ("timestamp", "datetime", "date", "time")
_ACCEPTED_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
)


def parse_timestamp(raw: str) -> datetime:
    """Parse the timestamp formats commonly exported by data vendors."""
    text = raw.strip()
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in _ACCEPTED_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised timestamp: {raw!r}")


def load_csv(path: str | Path) -> list[Bar]:
    """Load OHLCV bars from CSV, sorted by time. Bar timestamps are open times."""
    bars: list[Bar] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty file or missing header")
        lookup = {name.strip().lower(): name for name in reader.fieldnames}
        ts_key = next((lookup[f] for f in _TIMESTAMP_FIELDS if f in lookup), None)
        if ts_key is None:
            raise ValueError(f"{path}: no timestamp column found in {reader.fieldnames}")
        for row in reader:
            if not row.get(ts_key):
                continue
            bars.append(
                Bar(
                    timestamp=parse_timestamp(row[ts_key]),
                    open=float(row[lookup["open"]]),
                    high=float(row[lookup["high"]]),
                    low=float(row[lookup["low"]]),
                    close=float(row[lookup["close"]]),
                    volume=float(row.get(lookup.get("volume", ""), 0) or 0),
                )
            )
    bars.sort(key=lambda b: b.timestamp)
    return bars


def resample(bars: Sequence[Bar], minutes: int) -> list[Bar]:
    """
    Aggregate bars into a coarser timeframe (e.g. 1m -> 5m).

    Buckets are anchored to the hour, so a 15m resample yields :00 :15 :30 :45.
    Buckets never span a calendar day.
    """
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    out: list[Bar] = []
    bucket: list[Bar] = []
    bucket_start: Optional[datetime] = None

    def flush() -> None:
        if not bucket or bucket_start is None:
            return
        out.append(
            Bar(
                timestamp=bucket_start,
                open=bucket[0].open,
                high=max(b.high for b in bucket),
                low=min(b.low for b in bucket),
                close=bucket[-1].close,
                volume=sum(b.volume for b in bucket),
            )
        )

    for bar in bars:
        start = _bucket_start(bar.timestamp, minutes)
        if bucket_start is None or start != bucket_start:
            flush()
            bucket = []
            bucket_start = start
        bucket.append(bar)
    flush()
    return out


def _bucket_start(ts: datetime, minutes: int) -> datetime:
    total = ts.hour * 60 + ts.minute
    floored = (total // minutes) * minutes
    return ts.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)


def filter_session(
    bars: Iterable[Bar],
    start: time,
    end: time,
    weekdays_only: bool = True,
) -> list[Bar]:
    """Keep only bars whose open time falls inside [start, end)."""
    kept = []
    for bar in bars:
        if weekdays_only and bar.timestamp.weekday() >= 5:
            continue
        t = bar.timestamp.time()
        if start <= t < end:
            kept.append(bar)
    return kept


def group_by_day(bars: Iterable[Bar]) -> dict[date, list[Bar]]:
    """Bucket bars by calendar date, preserving order within each day."""
    days: dict[date, list[Bar]] = {}
    for bar in bars:
        days.setdefault(bar.timestamp.date(), []).append(bar)
    return days


def synthetic_bars(
    days: int = 60,
    start_date: date = date(2026, 1, 5),
    session_start: time = time(9, 30),
    session_end: time = time(16, 0),
    minutes: int = 5,
    start_price: float = 5000.0,
    bar_volatility_points: float = 3.0,
    trend_points_per_day: float = 1.5,
    gap_volatility_points: float = 8.0,
    seed: int = 42,
    tick_size: float = 0.25,
) -> list[Bar]:
    """
    Deterministic random-walk feed with overnight gaps and intraday drift.

    Not a substitute for real data — it exists so the engine, the strategy and
    the metrics can be run end-to-end (and regression-tested) offline.
    """
    rng = random.Random(seed)
    bars: list[Bar] = []
    price = start_price
    current = start_date
    produced = 0

    def snap(value: float) -> float:
        return round(round(value / tick_size) * tick_size, 10)

    while produced < days:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue
        price = max(1.0, price + rng.gauss(0, gap_volatility_points))
        day_drift = rng.gauss(trend_points_per_day, trend_points_per_day * 2) / max(
            1, _bars_per_session(session_start, session_end, minutes)
        )
        ts = datetime.combine(current, session_start)
        session_close = datetime.combine(current, session_end)
        while ts < session_close:
            open_ = price
            close = max(1.0, open_ + day_drift + rng.gauss(0, bar_volatility_points))
            high = max(open_, close) + abs(rng.gauss(0, bar_volatility_points * 0.6))
            low = min(open_, close) - abs(rng.gauss(0, bar_volatility_points * 0.6))
            bars.append(
                Bar(
                    timestamp=ts,
                    open=snap(open_),
                    high=snap(high),
                    low=snap(low),
                    close=snap(close),
                    volume=float(rng.randint(500, 5000)),
                )
            )
            price = close
            ts += timedelta(minutes=minutes)
        produced += 1
        current += timedelta(days=1)
    return bars


def _bars_per_session(start: time, end: time, minutes: int) -> int:
    span = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
    return max(1, span // minutes)


def iter_bars(bars: Sequence[Bar]) -> Iterator[Bar]:
    """Yield bars in order — the shape a live feed adapter should implement."""
    yield from bars
