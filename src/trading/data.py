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
import math
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

from src.trading.models import Bar

_TIMESTAMP_FIELDS = ("timestamp", "datetime", "date", "time", "local time", "gmt time")
_DATE_FIELDS = ("date", "day")
_TIME_FIELDS = ("time", "hour")
_OHLC_ALIASES = {
    "open": ("open", "o", "openprice", "open price"),
    "high": ("high", "h", "highprice", "high price"),
    "low": ("low", "l", "lowprice", "low price"),
    "close": ("close", "c", "closeprice", "close price", "last", "price"),
    "volume": ("volume", "vol", "v", "tickvol", "tick volume", "real volume"),
}
_ACCEPTED_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y.%m.%d %H:%M:%S",  # MetaTrader export
    "%Y.%m.%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%d.%m.%Y %H:%M:%S.%f",  # Dukascopy export
    "%Y-%m-%d",
    "%Y.%m.%d",
    "%d/%m/%Y",
)


def parse_timestamp(raw: str) -> datetime:
    """
    Parse the timestamp formats real broker and vendor exports actually use.

    Covers ISO, MetaTrader dots, European and US slashes, Dukascopy
    milliseconds, and Unix epochs in seconds or milliseconds (TradingView).

    Epochs are read as UTC and returned naive. Everything else is taken at face
    value. Since the bot compares bar times against session hours, the data must
    be exported in exchange local time — a timezone mistake silently shifts the
    opening range and the flat-at cutoff.
    """
    text = raw.strip().strip('"')
    if not text:
        raise ValueError("Empty timestamp")

    digits = text.replace(".", "")
    if digits.isdigit() and len(digits) in (10, 13):
        seconds = int(digits) / (1000 if len(digits) == 13 else 1)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None)

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in _ACCEPTED_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised timestamp: {raw!r}")


def _normalise(name: str) -> str:
    """MetaTrader writes '<OPEN>', some vendors 'Open Price' — flatten both."""
    return name.strip().strip("<>").strip().lower().replace("_", " ")


def _find(lookup: dict[str, str], names: tuple[str, ...]) -> Optional[str]:
    for name in names:
        if name in lookup:
            return lookup[name]
    return None


def _sniff_delimiter(sample: str) -> str:
    """Pick the separator by counting candidates in the header line."""
    header = sample.splitlines()[0] if sample else ""
    counts = {sep: header.count(sep) for sep in ("\t", ";", ",")}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def load_csv(path: str | Path) -> list[Bar]:
    """
    Load OHLCV bars from a delimited text file, sorted by time.

    Accepts comma, semicolon or tab separated files, MetaTrader-style
    `<DATE>`/`<TIME>` column pairs, and epoch or textual timestamps. Bar
    timestamps are OPEN times, in the market's local timezone — no conversion
    is performed, so export the data in exchange time.
    """
    with open(path, newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter=_sniff_delimiter(sample))
        if not reader.fieldnames:
            raise ValueError(f"{path}: empty file or missing header")

        lookup = {_normalise(name): name for name in reader.fieldnames if name}
        ts_key = _find(lookup, _TIMESTAMP_FIELDS)
        date_key = _find(lookup, _DATE_FIELDS)
        time_key = _find(lookup, _TIME_FIELDS)
        split_timestamp = date_key is not None and time_key is not None
        if ts_key is None and not split_timestamp:
            raise ValueError(
                f"{path}: no timestamp column found in {reader.fieldnames}"
            )

        columns = {
            field: _find(lookup, aliases) for field, aliases in _OHLC_ALIASES.items()
        }
        missing = [f for f in ("open", "high", "low", "close") if columns[f] is None]
        if missing:
            raise ValueError(f"{path}: missing column(s) {missing} in {reader.fieldnames}")

        bars: list[Bar] = []
        for line, row in enumerate(reader, start=2):
            if split_timestamp:
                raw = f"{row.get(date_key, '')} {row.get(time_key, '')}".strip()
            else:
                raw = (row.get(ts_key) or "").strip()
            if not raw or not (row.get(columns["close"]) or "").strip():
                continue  # blank or padding row
            try:
                bars.append(
                    Bar(
                        timestamp=parse_timestamp(raw),
                        open=float(row[columns["open"]]),
                        high=float(row[columns["high"]]),
                        low=float(row[columns["low"]]),
                        close=float(row[columns["close"]]),
                        volume=float(
                            (columns["volume"] and row.get(columns["volume"])) or 0
                        ),
                    )
                )
            except ValueError as exc:
                raise ValueError(f"{path}: line {line}: {exc}") from exc

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
    volatility_reference_minutes: int = 5,
) -> list[Bar]:
    """
    Deterministic random-walk feed with overnight gaps and intraday drift.

    `bar_volatility_points` describes a bar of `volatility_reference_minutes`
    and is scaled by the square root of time for other timeframes, so a 15m bar
    moves ~1.7x a 5m one. Without that scaling every timeframe would produce
    identically sized bars, which quietly invalidates any comparison between
    them — ATR-based stops would come out the same on 5m and 15m.

    Not a substitute for real data — it exists so the engine, the strategy and
    the metrics can be run end-to-end (and regression-tested) offline.
    """
    rng = random.Random(seed)
    scale = math.sqrt(minutes / max(1, volatility_reference_minutes))
    bar_volatility_points *= scale
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
