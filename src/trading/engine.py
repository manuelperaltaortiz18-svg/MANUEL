"""
The bot itself: a bar-driven loop wiring strategy, risk and broker together.

The same `on_bar` call drives a backtest (bars replayed from a file) and a live
session (bars pushed by a feed as they close), which is the point: what you
test is what you run.

Ordering inside a bar is deliberate:
  1. the broker matches orders that were already resting;
  2. fills are reported to strategy and risk;
  3. session rules (flat-at, entry cutoff) are applied;
  4. only then may a new bracket be submitted, for the *next* bar.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Optional

from src.config.trading_config import BotConfig
from src.trading.broker import Broker
from src.trading.models import Bar, ExitReason, Signal
from src.trading.risk import RiskManager
from src.trading.strategy import Strategy

Logger = Callable[[str], None]


class TradingBot:
    """Single-position intraday bot with a strictly symmetric bracket."""

    def __init__(
        self,
        config: BotConfig,
        strategy: Strategy,
        broker: Broker,
        risk: RiskManager,
        logger: Optional[Logger] = None,
    ) -> None:
        self.config = config
        self.session = config.session
        self.strategy = strategy
        self.broker = broker
        self.risk = risk
        self.logger = logger
        self._day: Optional[date] = None
        self._bar_duration = timedelta(minutes=config.timeframe_minutes)
        self.rejected_signals: list[tuple[datetime, str]] = []

    # -- main loop ---------------------------------------------------------

    def run(self, bars) -> None:
        """Replay a sequence of closed bars."""
        for bar in bars:
            self.on_bar(bar)
        self.finish()

    def on_bar(self, bar: Bar) -> None:
        ts = bar.timestamp
        if ts.date() != self._day:
            self._roll_session(ts.date(), ts)

        self.broker.on_bar(bar)
        self._drain_notifications()

        t = ts.time()
        if not self.session.is_in_session(t):
            return

        if self._crosses_flat_time(ts):
            self.broker.cancel_pending("session close")
            if self.broker.position is not None:
                self.broker.close_position(ExitReason.SESSION_CLOSE, ts)
                self._drain_notifications()
            return

        signal = self.strategy.on_bar(bar)

        if self.broker.position is not None:
            return

        if t >= self.session.entry_cutoff:
            self.broker.cancel_pending("entry cutoff")
            return

        if signal is None:
            return

        decision = self.risk.can_trade(self.broker.equity)
        if not decision:
            self.broker.cancel_pending(decision.reason)
            self._reject(ts, decision.reason)
            return

        qty = self.risk.position_size(self.broker.equity, signal.risk_points)
        if qty <= 0:
            self._reject(ts, f"size 0 for {signal.risk_points:.2f} pt stop")
            return

        self._submit(signal, qty, ts)

    def finish(self) -> None:
        """Flatten and cancel at the end of a replay so nothing is left open."""
        self.broker.cancel_pending("run finished")
        if self.broker.position is not None:
            self.broker.close_position(ExitReason.SESSION_CLOSE, datetime.now())
            self._drain_notifications()

    # -- internals ---------------------------------------------------------

    def _submit(self, signal: Signal, qty: float, now: datetime) -> None:
        pending = self.broker.pending_order
        if pending is not None:
            unchanged = (
                pending.side is signal.side
                and pending.entry_stop == signal.entry_stop
                and pending.stop_loss == signal.stop_loss
                and pending.take_profit == signal.take_profit
                and pending.entry_limit == signal.entry_limit
                and pending.qty == qty
            )
            if unchanged:
                return  # leave the resting order alone
            self.broker.cancel_pending("replaced by updated signal")

        order = self.broker.submit_bracket(
            side=signal.side,
            qty=qty,
            entry_stop=signal.entry_stop,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            now=now,
            entry_limit=signal.entry_limit,
            expires_at=signal.valid_until,
            tag=signal.reason,
        )
        self._log(
            f"{now:%Y-%m-%d %H:%M} armed {order.side.value} {qty:g} @ {order.entry_stop} "
            f"stop {order.stop_loss} target {order.take_profit} "
            f"(R:R {order.reward_risk_ratio:.2f})"
        )

    def _crosses_flat_time(self, ts: datetime) -> bool:
        """
        True when this bar is the last one that leaves the account flat in time.

        The test is on the bar's END, not its start, because `flat_at` is a
        deadline: closing on the bar that ends at 15:45 makes the account flat
        at 15:45. Comparing start times instead would, on a 15-minute
        timeframe, find no bar stamped 15:55 at all and skip the forced close
        entirely — leaking the position into the next session.
        """
        end = ts + self._bar_duration
        if end.date() != ts.date():
            return True
        return end.time() >= self.session.flat_at

    def _roll_session(self, day: date, now: datetime) -> None:
        self.broker.cancel_pending("new session")
        if self.broker.position is not None:
            self.broker.close_position(ExitReason.SESSION_CLOSE, now)
            self._drain_notifications()
        self._day = day
        self.risk.on_session_start(day, self.broker.equity)
        self.strategy.on_session_start(day)

    def _drain_notifications(self) -> None:
        for position in self.broker.drain_new_entries():
            self.risk.on_entry_filled()
            self.strategy.on_entry_filled(position)
            self._log(
                f"{position.entry_time:%Y-%m-%d %H:%M} filled {position.side.value} "
                f"{position.qty:g} @ {position.entry_price}"
            )
        for trade in self.broker.drain_new_trades():
            self.risk.on_trade_closed(trade)
            self.strategy.on_trade_closed(trade)
            self._log(
                f"{trade.exit_time:%Y-%m-%d %H:%M} exit {trade.exit_reason.value} "
                f"@ {trade.exit_price} pnl {trade.net_pnl:+.2f} ({trade.r_multiple:+.2f}R)"
            )

    def _reject(self, ts: datetime, reason: str) -> None:
        self.rejected_signals.append((ts, reason))

    def _log(self, message: str) -> None:
        if self.logger is not None:
            self.logger(message)
