"""
Core data models for the intraday trading bot: bars, instrument specs,
bracket orders, positions and closed trades.

All prices are expressed in index points (e.g. 5432.25 for the S&P 500).
Money is derived from points through `InstrumentSpec.point_value`.

Bar timestamp convention: a bar's `timestamp` is its OPEN time. A 5-minute
bar stamped 15:55 covers the interval [15:55, 16:00).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# Prices come from data feeds as floats; comparisons need a small tolerance.
PRICE_EPS = 1e-9


class Side(Enum):
    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> int:
        """+1 for long, -1 for short. Multiplies price deltas into P&L."""
        return 1 if self is Side.LONG else -1

    @property
    def opposite(self) -> "Side":
        return Side.SHORT if self is Side.LONG else Side.LONG


class ExitReason(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    SESSION_CLOSE = "session_close"
    MANUAL = "manual"


class EntryType(Enum):
    """
    How the entry reaches the market.

    STOP   — resting order above/below a level; only fills on a real breakout.
    MARKET — the signal was a bar CLOSE, so the order goes in at the next open.
    """

    STOP = "stop"
    MARKET = "market"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class RoundMode(Enum):
    NEAREST = "nearest"
    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class Bar:
    """A single OHLCV candle. Immutable — the feed is the source of truth."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.high < self.low - PRICE_EPS:
            raise ValueError(f"Bar {self.timestamp}: high {self.high} < low {self.low}")
        if self.high < max(self.open, self.close) - PRICE_EPS:
            raise ValueError(f"Bar {self.timestamp}: high {self.high} below open/close")
        if self.low > min(self.open, self.close) + PRICE_EPS:
            raise ValueError(f"Bar {self.timestamp}: low {self.low} above open/close")

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def is_up(self) -> bool:
        return self.close >= self.open


@dataclass(frozen=True)
class InstrumentSpec:
    """
    Contract specification for the traded S&P 500 vehicle.

    `point_value` is the currency amount earned per 1.0 index point per unit:
    50 for the ES future, 5 for the Micro (MES), 1 for a typical index CFD.
    `commission_per_unit` is charged per side (entry and exit each pay it).
    """

    symbol: str
    tick_size: float = 0.25
    point_value: float = 5.0
    qty_step: float = 1.0
    min_qty: float = 1.0
    commission_per_unit: float = 0.50
    slippage_ticks: float = 1.0
    currency: str = "USD"

    @property
    def slippage_points(self) -> float:
        return self.slippage_ticks * self.tick_size

    def round_price(self, price: float, mode: RoundMode = RoundMode.NEAREST) -> float:
        """Snap a price to the instrument's tick grid."""
        if self.tick_size <= 0:
            return price
        ticks = price / self.tick_size
        if mode is RoundMode.UP:
            ticks = math.ceil(ticks - PRICE_EPS)
        elif mode is RoundMode.DOWN:
            ticks = math.floor(ticks + PRICE_EPS)
        else:
            ticks = math.floor(ticks + 0.5)
        return round(ticks * self.tick_size, 10)

    def round_qty(self, qty: float) -> float:
        """Floor a size to the tradable step. Returns 0.0 below the minimum."""
        if qty <= 0 or self.qty_step <= 0:
            return 0.0
        steps = math.floor(qty / self.qty_step + PRICE_EPS)
        rounded = round(steps * self.qty_step, 10)
        return rounded if rounded >= self.min_qty - PRICE_EPS else 0.0

    def money(self, points: float, qty: float) -> float:
        """Convert a point move into currency for a given size."""
        return points * qty * self.point_value

    def commission(self, qty: float) -> float:
        """Commission for one side of a trade."""
        return self.commission_per_unit * qty


@dataclass
class BracketOrder:
    """
    A stop-entry order carrying its own protective stop and target.

    The bot never sends a naked entry: stop-loss and take-profit are attached
    up front so a disconnect can't leave an unprotected position.
    """

    id: str
    side: Side
    qty: float
    stop_loss: float
    created_at: datetime
    entry_type: EntryType = EntryType.STOP
    entry_stop: Optional[float] = None
    take_profit: Optional[float] = None
    reward_risk_ratio: float = 1.0
    entry_limit: Optional[float] = None
    max_risk_money: Optional[float] = None
    expires_at: Optional[datetime] = None
    tag: str = ""
    status: OrderStatus = OrderStatus.PENDING

    @property
    def risk_points(self) -> Optional[float]:
        """Planned risk, once the entry level is known. None for market entries."""
        if self.entry_stop is None:
            return None
        return abs(self.entry_stop - self.stop_loss)

    def target_for(self, fill_price: float) -> float:
        """
        The take-profit for an actual fill.

        A fixed `take_profit` is honoured as given. Otherwise the target is
        derived from the fill so the 1:1 stays exact no matter where the entry
        actually happened — the stop is a structural level, the target is not.
        """
        if self.take_profit is not None:
            return self.take_profit
        risk = abs(fill_price - self.stop_loss)
        return fill_price + risk * self.reward_risk_ratio * self.side.sign


@dataclass
class Position:
    """An open position with its resting bracket levels."""

    side: Side
    qty: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    planned_risk_points: float
    entry_commission: float = 0.0
    entry_slippage_points: float = 0.0
    tag: str = ""
    mae_points: float = 0.0  # maximum adverse excursion
    mfe_points: float = 0.0  # maximum favourable excursion

    @property
    def risk_points(self) -> float:
        return abs(self.entry_price - self.stop_loss)

    def unrealized_points(self, price: float) -> float:
        return (price - self.entry_price) * self.side.sign

    def update_excursions(self, high: float, low: float) -> None:
        best = self.unrealized_points(high if self.side is Side.LONG else low)
        worst = self.unrealized_points(low if self.side is Side.LONG else high)
        self.mfe_points = max(self.mfe_points, best)
        self.mae_points = min(self.mae_points, worst)


@dataclass
class Trade:
    """A completed round trip, with everything needed for post-hoc analysis."""

    symbol: str
    side: Side
    qty: float
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    exit_reason: ExitReason
    gross_pnl: float
    commission: float
    planned_risk_points: float
    point_value: float = 1.0
    entry_slippage_points: float = 0.0
    exit_slippage_points: float = 0.0
    mae_points: float = 0.0
    mfe_points: float = 0.0
    tag: str = ""

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.commission

    @property
    def friction(self) -> float:
        """
        Total execution cost: commissions plus modelled slippage.

        Slippage is already inside `gross_pnl`, so this is not subtracted
        again — it exists to state the true hurdle a 1:1 strategy must clear,
        which for spread-based vehicles (CFDs) is entirely slippage.
        """
        slip_points = self.entry_slippage_points + self.exit_slippage_points
        return self.commission + slip_points * self.qty * self.point_value

    @property
    def points(self) -> float:
        return (self.exit_price - self.entry_price) * self.side.sign

    @property
    def planned_risk_money(self) -> float:
        return self.planned_risk_points * self.qty * self.point_value

    @property
    def r_multiple(self) -> float:
        """Result in units of planned risk (net of costs)."""
        risk_money = self.planned_risk_money
        return self.net_pnl / risk_money if risk_money else 0.0

    @property
    def is_win(self) -> bool:
        return self.net_pnl > 0


@dataclass
class Signal:
    """
    A strategy's proposal for the next bar.

    `entry_stop` is a trigger level, not a market order: the breakout is only
    taken if price actually trades through it.
    """

    side: Side
    stop_loss: float
    reason: str
    entry_type: EntryType = EntryType.STOP
    entry_stop: Optional[float] = None
    take_profit: Optional[float] = None
    reward_risk_ratio: float = 1.0
    reference_price: Optional[float] = None  # expected fill for a market entry
    entry_limit: Optional[float] = None
    valid_until: Optional[datetime] = None
    meta: dict = field(default_factory=dict)

    @property
    def entry_reference(self) -> float:
        """Price the bracket is measured from: the trigger, or the last close."""
        if self.entry_stop is not None:
            return self.entry_stop
        if self.reference_price is None:
            raise ValueError("A market signal needs a reference_price for sizing")
        return self.reference_price

    @property
    def risk_points(self) -> float:
        return abs(self.entry_reference - self.stop_loss)

    @property
    def reward_points(self) -> float:
        target = self.take_profit
        if target is None:
            return self.risk_points * self.reward_risk_ratio
        return abs(target - self.entry_reference)

    @property
    def realised_reward_risk(self) -> float:
        return self.reward_points / self.risk_points if self.risk_points else 0.0
