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

from src.config.trading_config import (
    BreakoutConfig,
    FirstCandleBreakConfig,
    SessionConfig,
)
from src.trading.indicators import RollingExtremes, WilderATR, ema
from src.trading.models import (
    Bar,
    EntryType,
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
            stop_loss=self.instrument.round_price(stop_loss),
            reason=f"{self.config.mode} breakout ({side.value})",
            entry_stop=entry,
            take_profit=self.instrument.round_price(take_profit),
            reward_risk_ratio=self.config.reward_risk_ratio,
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


class FirstCandleBreakStrategy(Strategy):
    """
    The session's first candle defines a range; the first candle to CLOSE
    outside it takes the trade — long above the high, short below the low.

    Closing outside is a stricter trigger than touching the level. A candle can
    spike through the range and close back inside; that is not a signal here,
    which is the whole difference from a stop-order breakout.

    With `require_excursion` the strategy waits instead for the failed move:
    price must close outside, close back inside, and only then does the next
    close outside trigger — so a break up that fails and closes below the low
    becomes a short.

    Execution differs from the breakout strategy in two ways that matter:

    * The trigger is a CLOSE, not a level being touched, so the entry is a
      market order at the next open rather than a resting stop. There is no
      pretending we got filled at the close we used to decide.
    * The stop is structural — the far side of the range, plus a buffer — not a
      volatility multiple. The target is then computed from the actual fill so
      the 1:1 holds exactly, whatever the open gave us.
    """

    def __init__(
        self,
        config: FirstCandleBreakConfig,
        instrument: InstrumentSpec,
        session: SessionConfig,
    ) -> None:
        self.config = config
        self.instrument = instrument
        self.session = session

        self._session_open: Optional[datetime] = None
        self._range_complete = False
        self._range_high: Optional[float] = None
        self._range_low: Optional[float] = None
        self._left_range = False
        self._returned = False
        self._entries_today = 0

    # -- lifecycle ---------------------------------------------------------

    def on_session_start(self, day: date) -> None:
        self._session_open = None
        self._range_complete = False
        self._range_high = None
        self._range_low = None
        self._left_range = False
        self._returned = False
        self._entries_today = 0

    def on_entry_filled(self, position: Position) -> None:
        self._entries_today += 1

    # -- state -------------------------------------------------------------

    @property
    def range_high(self) -> Optional[float]:
        return self._range_high

    @property
    def range_low(self) -> Optional[float]:
        return self._range_low

    @property
    def armed(self) -> bool:
        """True when a close outside the range would trigger a trade."""
        if self._range_high is None or not self._range_complete:
            return False
        return self._returned or not self.config.require_excursion

    # -- signal generation -------------------------------------------------

    def on_bar(self, bar: Bar) -> Optional[Signal]:
        if self._session_open is None:
            self._session_open = bar.timestamp

        # Measured in minutes from the open, not in bars: the same range comes
        # out on any timeframe, and a missing bar at the open cannot shift it.
        minutes_in = (bar.timestamp - self._session_open).total_seconds() / 60.0
        if minutes_in < self.config.range_minutes:
            self._range_high = bar.high if self._range_high is None else max(self._range_high, bar.high)
            self._range_low = bar.low if self._range_low is None else min(self._range_low, bar.low)
            return None  # the range candles themselves never trade
        self._range_complete = True

        if self._range_high is None or self._range_low is None:
            return None
        if self._entries_today >= self.config.max_signals_per_day:
            return None

        above = bar.close > self._range_high
        below = bar.close < self._range_low
        outside = above or below

        # State machine: out of the range, back inside, then out again.
        if not self._left_range:
            if outside:
                self._left_range = True
            if self.config.require_excursion:
                return None
        elif not self._returned:
            if not outside:
                self._returned = True
            return None

        if not outside:
            return None

        width = self._range_high - self._range_low
        if width < self.config.min_range_points:
            return None
        if self.config.max_range_points and width > self.config.max_range_points:
            return None

        side = Side.LONG if above else Side.SHORT
        if side is Side.LONG and not self.config.allow_long:
            return None
        if side is Side.SHORT and not self.config.allow_short:
            return None

        buffer_points = self.config.stop_buffer_ticks * self.instrument.tick_size
        if side is Side.LONG:
            stop_loss = self.instrument.round_price(
                self._range_low - buffer_points, RoundMode.DOWN
            )
        else:
            stop_loss = self.instrument.round_price(
                self._range_high + buffer_points, RoundMode.UP
            )

        return Signal(
            side=side,
            stop_loss=stop_loss,
            reason=f"first-candle break ({side.value})",
            entry_type=EntryType.MARKET,
            reward_risk_ratio=self.config.reward_risk_ratio,
            # Sizing needs a price before the fill exists; the close we just
            # confirmed on is the honest estimate of where we get in.
            reference_price=bar.close,
            valid_until=None,
            meta={
                "range_high": self._range_high,
                "range_low": self._range_low,
                "range_width": width,
                "confirming_close": bar.close,
            },
        )
