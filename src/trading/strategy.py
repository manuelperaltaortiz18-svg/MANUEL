"""
Range-breakout strategy with a strictly symmetric 1:1 bracket.

The 1:1 payoff is the defining constraint: every trade risks exactly what it
aims to make, so the strategy is only profitable if it wins meaningfully more
than half of its attempts *after* costs. `breakeven_hit_rate()` in
`src.trading.metrics` makes that hurdle explicit.

Signals are produced from CLOSED bars only, and are expressed as stop-entry
levels for the NEXT bar — the bot never assumes it can trade at a price it has
already seen.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from datetime import date, datetime
from typing import Optional

from src.config.trading_config import BreakoutConfig, SessionConfig
from src.trading.indicators import RollingExtremes, WilderATR, ema
from src.trading.models import (
    Bar,
    InstrumentSpec,
    Position,
    RoundMode,
    Side,
    Signal,
    Trade,
)


class Strategy(ABC):
    """Interface every strategy must implement to be driven by `TradingBot`."""

    @abstractmethod
    def on_bar(self, bar: Bar) -> Optional[Signal]:
        """Consume a closed in-session bar and optionally propose an entry."""

    def on_session_start(self, day: date) -> None:
        """Reset per-session state. Called before the first bar of each day."""

    def on_entry_filled(self, position: Position) -> None:
        """Notification that a proposed bracket was actually filled."""

    def on_trade_closed(self, trade: Trade) -> None:
        """Notification that a position was closed."""


class BreakoutStrategy(Strategy):
    """
    Opening-range or Donchian breakout with an ATR- (or range-) sized stop and
    a take-profit at the same distance.

    Direction selection: when both sides are enabled, the strategy arms the
    side price is currently leaning towards (close above the range midpoint =>
    long side armed). The bot replaces the resting order as that lean changes,
    so an unfilled order follows price around the range instead of going stale.
    """

    def __init__(
        self,
        config: BreakoutConfig,
        instrument: InstrumentSpec,
        session: SessionConfig,
    ) -> None:
        self.config = config
        self.instrument = instrument
        self.session = session

        self._atr = WilderATR(config.atr_period)
        self._donchian = RollingExtremes(config.lookback_bars)
        self._closes: deque[float] = deque(maxlen=max(4 * config.trend_filter_period, 4))

        self._day: Optional[date] = None
        self._or_high: Optional[float] = None
        self._or_low: Optional[float] = None
        self._or_complete = False
        self._entries_today = 0

    # -- lifecycle ---------------------------------------------------------

    def on_session_start(self, day: date) -> None:
        self._day = day
        self._or_high = None
        self._or_low = None
        self._or_complete = False
        self._entries_today = 0
        # ATR and Donchian intentionally carry across days: overnight gaps are
        # part of the volatility the stop has to absorb.

    def on_entry_filled(self, position: Position) -> None:
        self._entries_today += 1

    # -- signal generation -------------------------------------------------

    def on_bar(self, bar: Bar) -> Optional[Signal]:
        self._atr.update(bar)
        self._donchian.update(bar)
        self._closes.append(bar.close)
        self._update_opening_range(bar)

        if self._entries_today >= self.config.max_signals_per_day:
            return None

        levels = self._breakout_levels()
        if levels is None:
            return None
        upper, lower = levels

        width = upper - lower
        if width < self.config.min_range_points:
            return None

        stop_distance = self._stop_distance(width)
        if stop_distance is None:
            return None

        side = self._preferred_side(bar, upper, lower)
        if side is None:
            return None

        buffer_points = self.config.breakout_buffer_ticks * self.instrument.tick_size
        if side is Side.LONG:
            entry = self.instrument.round_price(upper + buffer_points, RoundMode.UP)
            stop_loss = entry - stop_distance
            take_profit = entry + stop_distance * self.config.reward_risk_ratio
        else:
            entry = self.instrument.round_price(lower - buffer_points, RoundMode.DOWN)
            stop_loss = entry + stop_distance
            take_profit = entry - stop_distance * self.config.reward_risk_ratio

        return Signal(
            side=side,
            entry_stop=entry,
            stop_loss=self.instrument.round_price(stop_loss),
            take_profit=self.instrument.round_price(take_profit),
            reason=f"{self.config.mode} breakout ({side.value})",
            entry_limit=self._entry_limit(side, entry),
            valid_until=self._session_deadline(bar.timestamp),
            meta={
                "range_high": upper,
                "range_low": lower,
                "range_width": width,
                "stop_distance": stop_distance,
                "atr": self._atr.value,
            },
        )

    # -- internals ---------------------------------------------------------

    def _update_opening_range(self, bar: Bar) -> None:
        if self.config.mode != "opening_range" or self._or_complete:
            return
        if bar.timestamp.time() < self.session.opening_range_end:
            self._or_high = bar.high if self._or_high is None else max(self._or_high, bar.high)
            self._or_low = bar.low if self._or_low is None else min(self._or_low, bar.low)
        elif self._or_high is not None:
            self._or_complete = True

    def _breakout_levels(self) -> Optional[tuple[float, float]]:
        """Upper and lower breakout levels, or None while still forming."""
        if self.config.mode == "opening_range":
            if not self._or_complete or self._or_high is None or self._or_low is None:
                return None
            return self._or_high, self._or_low
        if not self._donchian.is_ready:
            return None
        upper, lower = self._donchian.highest, self._donchian.lowest
        if upper is None or lower is None:
            return None
        return upper, lower

    def _stop_distance(self, range_width: float) -> Optional[float]:
        if self.config.stop_mode == "atr":
            atr_value = self._atr.value
            if atr_value is None or atr_value <= 0:
                return None
            raw = atr_value * self.config.atr_multiple
        else:
            if range_width <= 0:
                return None
            raw = range_width * self.config.range_multiple

        clamped = min(max(raw, self.config.min_stop_points), self.config.max_stop_points)
        # Snapping the distance to the tick grid keeps entry, stop and target on
        # the grid too, which is what makes the 1:1 exact rather than approximate.
        distance = self.instrument.round_price(clamped, RoundMode.UP)
        return distance if distance > 0 else None

    def _preferred_side(self, bar: Bar, upper: float, lower: float) -> Optional[Side]:
        midpoint = (upper + lower) / 2
        wants_long = bar.close >= midpoint

        if not self._passes_trend_filter(Side.LONG if wants_long else Side.SHORT):
            # Try the other side before giving up on the bar.
            wants_long = not wants_long
            if not self._passes_trend_filter(Side.LONG if wants_long else Side.SHORT):
                return None

        if wants_long and self.config.allow_long:
            return Side.LONG
        if not wants_long and self.config.allow_short:
            return Side.SHORT
        # Requested side disabled: fall back to the enabled one if the filter allows.
        fallback = Side.SHORT if wants_long else Side.LONG
        if (fallback is Side.LONG and self.config.allow_long) or (
            fallback is Side.SHORT and self.config.allow_short
        ):
            return fallback if self._passes_trend_filter(fallback) else None
        return None

    def _passes_trend_filter(self, side: Side) -> bool:
        period = self.config.trend_filter_period
        if period <= 0:
            return True
        reference = ema(list(self._closes), period)
        if reference is None:
            return False
        last = self._closes[-1]
        return last >= reference if side is Side.LONG else last <= reference

    def _entry_limit(self, side: Side, entry: float) -> Optional[float]:
        """
        Worst price the breakout may be filled at.

        A gap far through the trigger would hand us a position whose target is
        already gone, so the entry is a stop-limit rather than a stop-market.

        The limit can never be tighter than the instrument's own execution
        friction — on a wide-spread CFD that would reject every fill.
        """
        ticks = self.config.max_entry_slippage_ticks
        if ticks <= 0:
            return None
        ticks = max(ticks, self.instrument.slippage_ticks)
        offset = ticks * self.instrument.tick_size
        raw = entry + offset if side is Side.LONG else entry - offset
        return self.instrument.round_price(
            raw, RoundMode.UP if side is Side.LONG else RoundMode.DOWN
        )

    def _session_deadline(self, ts: datetime) -> datetime:
        return datetime.combine(ts.date(), self.session.flat_at)
