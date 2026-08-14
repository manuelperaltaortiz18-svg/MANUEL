"""
Configuration for the intraday S&P 500 trading bot (1:1 risk/reward breakout).

This module is intentionally separate from the long-term investment system's
constants: the bot is a short-horizon execution tool and must never be used to
justify changes to the strategic allocation (CLAUDE.md §2, §42).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

from src.trading.models import InstrumentSpec

# --- Instrument presets -----------------------------------------------------
# point_value = currency per 1.0 index point per unit.

ES_FUTURE = InstrumentSpec(
    symbol="ES",
    tick_size=0.25,
    point_value=50.0,
    qty_step=1.0,
    min_qty=1.0,
    commission_per_unit=2.10,  # round-turn ~4.20 USD, charged per side
    slippage_ticks=1.0,
    currency="USD",
)

MES_FUTURE = InstrumentSpec(
    symbol="MES",
    tick_size=0.25,
    point_value=5.0,
    qty_step=1.0,
    min_qty=1.0,
    commission_per_unit=0.62,
    slippage_ticks=1.0,
    currency="USD",
)

SP500_CFD = InstrumentSpec(
    symbol="US500",
    tick_size=0.1,
    point_value=1.0,
    qty_step=0.1,
    min_qty=0.1,
    commission_per_unit=0.0,  # cost sits in the spread; model it as slippage
    slippage_ticks=5.0,
    currency="USD",
)

SPY_ETF = InstrumentSpec(
    symbol="SPY",
    tick_size=0.01,
    point_value=1.0,
    qty_step=1.0,
    min_qty=1.0,
    commission_per_unit=0.005,
    slippage_ticks=1.0,
    currency="USD",
)

INSTRUMENTS = {
    spec.symbol: spec for spec in (ES_FUTURE, MES_FUTURE, SP500_CFD, SPY_ETF)
}


# --- Session ----------------------------------------------------------------


@dataclass(frozen=True)
class SessionConfig:
    """
    Regular US cash session, expressed in the timezone of the incoming bars.

    Bars are assumed to already be in exchange local time (US/Eastern for the
    RTH defaults below); the bot does no timezone conversion.
    """

    session_start: time = time(9, 30)
    session_end: time = time(16, 0)
    entry_cutoff: time = time(15, 30)  # no new brackets submitted after this
    flat_at: time = time(15, 45)  # force-close any open position
    opening_range_minutes: int = 30  # two bars on the default 15m timeframe

    def __post_init__(self) -> None:
        if not self.session_start < self.entry_cutoff <= self.flat_at <= self.session_end:
            raise ValueError(
                "Session times must satisfy: start < entry_cutoff <= flat_at <= end"
            )
        if self.opening_range_minutes <= 0:
            raise ValueError("opening_range_minutes must be positive")

    def is_in_session(self, t: time) -> bool:
        return self.session_start <= t < self.session_end

    @property
    def opening_range_end(self) -> time:
        total = (
            self.session_start.hour * 60
            + self.session_start.minute
            + self.opening_range_minutes
        )
        return time(hour=(total // 60) % 24, minute=total % 60)


# --- Risk -------------------------------------------------------------------


@dataclass(frozen=True)
class RiskConfig:
    """
    Position sizing and circuit breakers.

    With a 1:1 payoff the edge lives entirely in the hit rate, so the guardrails
    below matter more than usual: a losing streak cannot be recovered by a
    single outsized winner.
    """

    risk_per_trade_pct: float = 0.5  # % of current equity risked per trade
    max_trades_per_day: int = 3
    max_consecutive_losses: int = 3  # stop for the day after this many
    daily_loss_limit_pct: float = 2.0  # stop for the day at this drawdown
    daily_profit_target_pct: float = 0.0  # 0 disables the target
    max_units: float = 0.0  # 0 = uncapped size (risk % still applies)
    min_equity: float = 0.0  # stop trading entirely below this equity

    def __post_init__(self) -> None:
        if self.risk_per_trade_pct <= 0:
            raise ValueError("risk_per_trade_pct must be positive")
        if self.max_trades_per_day <= 0:
            raise ValueError("max_trades_per_day must be positive")


# --- Strategy ---------------------------------------------------------------


@dataclass(frozen=True)
class BreakoutConfig:
    """
    Range-breakout entry with a strictly symmetric (1:1) bracket.

    mode:
      "opening_range" — trade a break of the first N minutes of the session.
      "donchian"      — trade a break of the highest high / lowest low of the
                        last `lookback_bars` completed bars.

    stop_mode:
      "atr"   — stop distance = atr_multiple * ATR(atr_period)
      "range" — stop distance = range_multiple * width of the broken range
    """

    mode: str = "opening_range"
    lookback_bars: int = 12
    atr_period: int = 14
    atr_multiple: float = 1.0
    range_multiple: float = 1.0
    stop_mode: str = "atr"
    breakout_buffer_ticks: float = 1.0
    max_entry_slippage_ticks: float = 4.0  # stop-limit guard; 0 disables it
    reward_risk_ratio: float = 1.0  # 1:1 — the whole point of this strategy
    min_stop_points: float = 2.0
    max_stop_points: float = 40.0
    allow_long: bool = True
    allow_short: bool = True
    max_signals_per_day: int = 2
    trend_filter_period: int = 0  # 0 disables; else EMA on closes
    min_range_points: float = 0.0  # skip sessions with a too-narrow range

    def __post_init__(self) -> None:
        if self.mode not in ("opening_range", "donchian"):
            raise ValueError(f"Unknown breakout mode: {self.mode}")
        if self.stop_mode not in ("atr", "range"):
            raise ValueError(f"Unknown stop mode: {self.stop_mode}")
        if self.reward_risk_ratio <= 0:
            raise ValueError("reward_risk_ratio must be positive")
        if self.min_stop_points <= 0 or self.max_stop_points < self.min_stop_points:
            raise ValueError("Invalid stop distance bounds")
        if not (self.allow_long or self.allow_short):
            raise ValueError("At least one direction must be enabled")


@dataclass(frozen=True)
class BotConfig:
    """Everything needed to run a backtest or a live session."""

    instrument: InstrumentSpec = MES_FUTURE
    session: SessionConfig = field(default_factory=SessionConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategy: BreakoutConfig = field(default_factory=BreakoutConfig)
    starting_equity: float = 25_000.0
    timeframe_minutes: int = 15


DEFAULT_CONFIG = BotConfig()
