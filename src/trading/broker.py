"""
Broker layer.

`Broker` is the interface the bot talks to — the same code path runs a
backtest, a paper session and (once an adapter is written) a live account.
`SimulatedBroker` is the built-in matching engine used for both backtesting and
paper trading against a live feed.

Writing a real adapter means subclassing `Broker` and mapping five operations
onto the venue's API: read equity, read position, submit a bracket, cancel the
resting order, flatten. `on_bar` stays a no-op there, since the venue does its
own matching; the adapter instead pushes filled entries and closed trades into
`_new_entries` / `_new_trades` so the bot's bookkeeping stays identical.
"""
from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.trading.models import (
    Bar,
    BracketOrder,
    ExitReason,
    InstrumentSpec,
    OrderStatus,
    Position,
    RoundMode,
    Side,
    Trade,
)


class Broker(ABC):
    """Minimal execution interface required by `TradingBot`."""

    def __init__(self, instrument: InstrumentSpec) -> None:
        self.instrument = instrument
        self._new_entries: list[Position] = []
        self._new_trades: list[Trade] = []

    # -- state -------------------------------------------------------------

    @property
    @abstractmethod
    def equity(self) -> float:
        """Account equity in the instrument's currency."""

    @property
    @abstractmethod
    def position(self) -> Optional[Position]:
        """The open position, if any. This bot holds at most one."""

    @property
    @abstractmethod
    def pending_order(self) -> Optional[BracketOrder]:
        """The resting stop-entry order, if any."""

    # -- actions -----------------------------------------------------------

    @abstractmethod
    def submit_bracket(
        self,
        side: Side,
        qty: float,
        entry_stop: float,
        stop_loss: float,
        take_profit: float,
        now: datetime,
        entry_limit: Optional[float] = None,
        expires_at: Optional[datetime] = None,
        tag: str = "",
    ) -> BracketOrder:
        """
        Place a stop entry with attached stop-loss and take-profit.

        `entry_limit` turns the entry into a stop-limit: the trade is skipped
        rather than filled at a price worse than that level.
        """

    @abstractmethod
    def cancel_pending(self, reason: str = "") -> None:
        """Cancel the resting entry order, if there is one."""

    @abstractmethod
    def close_position(self, reason: ExitReason, now: datetime) -> Optional[Trade]:
        """Flatten at market."""

    def on_bar(self, bar: Bar) -> None:
        """Feed a closed bar. No-op for venues that do their own matching."""

    # -- notifications -----------------------------------------------------

    def drain_new_entries(self) -> list[Position]:
        entries, self._new_entries = self._new_entries, []
        return entries

    def drain_new_trades(self) -> list[Trade]:
        trades, self._new_trades = self._new_trades, []
        return trades


class SimulatedBroker(Broker):
    """
    Bar-driven matching engine with deliberately pessimistic assumptions:

    * Entries fill only if price trades through the stop level, at the worse of
      the level and the bar open, plus slippage.
    * When a bar's range contains both the stop-loss and the take-profit, the
      stop is assumed to have been hit first. Intrabar order is unknowable from
      OHLC alone; assuming the good outcome is how backtests lie.
    * Gaps beyond a stop fill at the open, not at the stop price.
    * Commission is charged on both sides; take-profit (limit) fills pay no
      slippage, stop and market fills do.
    """

    def __init__(self, instrument: InstrumentSpec, starting_equity: float) -> None:
        super().__init__(instrument)
        self.starting_equity = starting_equity
        self._equity = starting_equity
        self._position: Optional[Position] = None
        self._pending: Optional[BracketOrder] = None
        self._last_bar: Optional[Bar] = None
        self._ids = itertools.count(1)
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple[datetime, float]] = []

    # -- state -------------------------------------------------------------

    @property
    def equity(self) -> float:
        return self._equity

    @property
    def position(self) -> Optional[Position]:
        return self._position

    @property
    def pending_order(self) -> Optional[BracketOrder]:
        return self._pending

    # -- actions -----------------------------------------------------------

    def submit_bracket(
        self,
        side: Side,
        qty: float,
        entry_stop: float,
        stop_loss: float,
        take_profit: float,
        now: datetime,
        entry_limit: Optional[float] = None,
        expires_at: Optional[datetime] = None,
        tag: str = "",
    ) -> BracketOrder:
        if self._position is not None:
            raise RuntimeError("Cannot submit an entry while a position is open")
        if qty <= 0:
            raise ValueError("qty must be positive")
        if side is Side.LONG and not (stop_loss < entry_stop < take_profit):
            raise ValueError("Long bracket must satisfy stop < entry < target")
        if side is Side.SHORT and not (take_profit < entry_stop < stop_loss):
            raise ValueError("Short bracket must satisfy target < entry < stop")
        if entry_limit is not None:
            if side is Side.LONG and entry_limit < entry_stop:
                raise ValueError("Long entry limit must sit at or above the stop level")
            if side is Side.SHORT and entry_limit > entry_stop:
                raise ValueError("Short entry limit must sit at or below the stop level")

        self._pending = BracketOrder(
            id=f"ord-{next(self._ids)}",
            side=side,
            qty=qty,
            entry_stop=entry_stop,
            stop_loss=stop_loss,
            take_profit=take_profit,
            created_at=now,
            entry_limit=entry_limit,
            expires_at=expires_at,
            tag=tag,
        )
        return self._pending

    def cancel_pending(self, reason: str = "") -> None:
        if self._pending is not None:
            self._pending.status = OrderStatus.CANCELLED
            self._pending = None

    def close_position(self, reason: ExitReason, now: datetime) -> Optional[Trade]:
        if self._position is None or self._last_bar is None:
            return None
        slip = self.instrument.slippage_points
        price = self._last_bar.close - slip * self._position.side.sign
        return self._exit(price, reason, now, slip)

    # -- matching ----------------------------------------------------------

    def on_bar(self, bar: Bar) -> None:
        self._last_bar = bar

        if self._position is not None:
            self._position.update_excursions(bar.high, bar.low)
            self._check_exits(bar)

        if self._position is None and self._pending is not None:
            if self._pending.expires_at is not None and bar.timestamp >= self._pending.expires_at:
                self._pending.status = OrderStatus.EXPIRED
                self._pending = None
            else:
                filled = self._check_entry(bar)
                if filled:
                    # The same bar can still take the position out; evaluating
                    # exits here is what stops a backtest from banking a win it
                    # never had.
                    self._check_exits(bar)

    def _check_entry(self, bar: Bar) -> bool:
        order = self._pending
        assert order is not None
        slip = self.instrument.slippage_points

        if order.side is Side.LONG:
            if bar.high < order.entry_stop:
                return False
            fill = max(order.entry_stop, bar.open) + slip
        else:
            if bar.low > order.entry_stop:
                return False
            fill = min(order.entry_stop, bar.open) - slip

        fill = self.instrument.round_price(
            fill, RoundMode.UP if order.side is Side.LONG else RoundMode.DOWN
        )
        if order.entry_limit is not None:
            too_far = (
                fill > order.entry_limit
                if order.side is Side.LONG
                else fill < order.entry_limit
            )
            if too_far:
                # Stop-limit: price ran away from the level. Skipping the trade
                # beats entering so far in that the 1:1 bracket is already spent.
                return False
        commission = self.instrument.commission(order.qty)
        self._position = Position(
            side=order.side,
            qty=order.qty,
            entry_price=fill,
            entry_time=bar.timestamp,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            planned_risk_points=order.risk_points,
            entry_commission=commission,
            entry_slippage_points=slip,
            tag=order.tag,
        )
        self._position.update_excursions(bar.high, bar.low)
        order.status = OrderStatus.FILLED
        self._pending = None
        self._new_entries.append(self._position)
        return True

    def _check_exits(self, bar: Bar) -> None:
        pos = self._position
        assert pos is not None
        slip = self.instrument.slippage_points

        if pos.side is Side.LONG:
            gapped_through_stop = bar.open <= pos.stop_loss
            stop_hit = bar.low <= pos.stop_loss
            target_hit = bar.high >= pos.take_profit
            if gapped_through_stop:
                self._exit(bar.open, ExitReason.STOP_LOSS, bar.timestamp)
            elif stop_hit:
                self._exit(pos.stop_loss - slip, ExitReason.STOP_LOSS, bar.timestamp, slip)
            elif target_hit:
                price = max(pos.take_profit, bar.open)
                self._exit(price, ExitReason.TAKE_PROFIT, bar.timestamp)
        else:
            gapped_through_stop = bar.open >= pos.stop_loss
            stop_hit = bar.high >= pos.stop_loss
            target_hit = bar.low <= pos.take_profit
            if gapped_through_stop:
                self._exit(bar.open, ExitReason.STOP_LOSS, bar.timestamp)
            elif stop_hit:
                self._exit(pos.stop_loss + slip, ExitReason.STOP_LOSS, bar.timestamp, slip)
            elif target_hit:
                price = min(pos.take_profit, bar.open)
                self._exit(price, ExitReason.TAKE_PROFIT, bar.timestamp)

    def _exit(
        self,
        price: float,
        reason: ExitReason,
        when: datetime,
        slippage_points: float = 0.0,
    ) -> Trade:
        pos = self._position
        assert pos is not None
        exit_price = self.instrument.round_price(price)
        points = (exit_price - pos.entry_price) * pos.side.sign
        gross = self.instrument.money(points, pos.qty)
        commission = pos.entry_commission + self.instrument.commission(pos.qty)

        trade = Trade(
            symbol=self.instrument.symbol,
            side=pos.side,
            qty=pos.qty,
            entry_time=pos.entry_time,
            entry_price=pos.entry_price,
            exit_time=when,
            exit_price=exit_price,
            exit_reason=reason,
            gross_pnl=gross,
            commission=commission,
            planned_risk_points=pos.planned_risk_points,
            point_value=self.instrument.point_value,
            entry_slippage_points=pos.entry_slippage_points,
            exit_slippage_points=slippage_points,
            mae_points=pos.mae_points,
            mfe_points=pos.mfe_points,
            tag=pos.tag,
        )
        self._equity += trade.net_pnl
        self.trades.append(trade)
        self._new_trades.append(trade)
        self.equity_curve.append((when, self._equity))
        self._position = None
        return trade
