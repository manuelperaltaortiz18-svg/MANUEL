"""
Indicators for the intraday breakout bot.

Two flavours are provided:
  * pure functions over a sequence of bars — convenient for tests and research;
  * incremental classes (`WilderATR`, `RollingExtremes`) — O(1) per bar, used by
    the live/backtest loop so cost doesn't grow with session length.
"""
from __future__ import annotations

from collections import deque
from typing import Optional, Sequence

from src.trading.models import Bar


def sma(values: Sequence[float], period: int) -> Optional[float]:
    """Simple moving average of the last `period` values."""
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def ema(values: Sequence[float], period: int) -> Optional[float]:
    """Exponential moving average, seeded with the SMA of the first window."""
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None
    k = 2.0 / (period + 1)
    current = sum(values[:period]) / period
    for value in values[period:]:
        current = value * k + current * (1 - k)
    return current


def true_range(bar: Bar, prev_close: Optional[float]) -> float:
    """Wilder's true range: the widest of the three candidate ranges."""
    if prev_close is None:
        return bar.high - bar.low
    return max(
        bar.high - bar.low,
        abs(bar.high - prev_close),
        abs(bar.low - prev_close),
    )


def atr(bars: Sequence[Bar], period: int) -> Optional[float]:
    """Average true range (Wilder smoothing) over the whole sequence."""
    tracker = WilderATR(period)
    value = None
    for bar in bars:
        value = tracker.update(bar)
    return value


def highest_high(bars: Sequence[Bar], period: int, offset: int = 0) -> Optional[float]:
    """Highest high of `period` bars ending `offset` bars back from the last."""
    window = _window(bars, period, offset)
    return max(b.high for b in window) if window else None


def lowest_low(bars: Sequence[Bar], period: int, offset: int = 0) -> Optional[float]:
    """Lowest low of `period` bars ending `offset` bars back from the last."""
    window = _window(bars, period, offset)
    return min(b.low for b in window) if window else None


def _window(bars: Sequence[Bar], period: int, offset: int) -> Sequence[Bar]:
    if period <= 0:
        raise ValueError("period must be positive")
    end = len(bars) - offset
    start = end - period
    if start < 0 or end <= 0:
        return []
    return bars[start:end]


class WilderATR:
    """Incremental ATR. Returns None until `period` bars have been seen."""

    def __init__(self, period: int) -> None:
        if period <= 0:
            raise ValueError("period must be positive")
        self.period = period
        self._prev_close: Optional[float] = None
        self._seed: list[float] = []
        self._value: Optional[float] = None

    @property
    def value(self) -> Optional[float]:
        return self._value

    def update(self, bar: Bar) -> Optional[float]:
        tr = true_range(bar, self._prev_close)
        self._prev_close = bar.close
        if self._value is None:
            self._seed.append(tr)
            if len(self._seed) == self.period:
                self._value = sum(self._seed) / self.period
        else:
            self._value = (self._value * (self.period - 1) + tr) / self.period
        return self._value

    def reset(self) -> None:
        self._prev_close = None
        self._seed.clear()
        self._value = None


class RollingExtremes:
    """Rolling highest-high / lowest-low over a fixed window of bars."""

    def __init__(self, period: int) -> None:
        if period <= 0:
            raise ValueError("period must be positive")
        self.period = period
        self._bars: deque[Bar] = deque(maxlen=period)

    @property
    def is_ready(self) -> bool:
        return len(self._bars) == self.period

    @property
    def highest(self) -> Optional[float]:
        return max((b.high for b in self._bars), default=None)

    @property
    def lowest(self) -> Optional[float]:
        return min((b.low for b in self._bars), default=None)

    def update(self, bar: Bar) -> None:
        self._bars.append(bar)

    def reset(self) -> None:
        self._bars.clear()
