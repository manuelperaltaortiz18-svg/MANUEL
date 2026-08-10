"""
Position sizing and daily circuit breakers.

Sizing is risk-first: the stop distance decides the size, never the other way
round. A wider stop buys fewer units so that the monetary risk of every trade
is the same fraction of equity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.config.trading_config import RiskConfig
from src.trading.models import InstrumentSpec, Trade


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.allowed


class RiskManager:
    """Tracks per-session state and answers 'may I trade, and how big?'."""

    def __init__(self, config: RiskConfig, instrument: InstrumentSpec) -> None:
        self.config = config
        self.instrument = instrument
        self.day: Optional[date] = None
        self.trades_today = 0
        self.consecutive_losses = 0
        self.day_start_equity = 0.0
        self.day_pnl = 0.0

    # -- lifecycle ---------------------------------------------------------

    def on_session_start(self, day: date, equity: float) -> None:
        self.day = day
        self.trades_today = 0
        self.consecutive_losses = 0
        self.day_start_equity = equity
        self.day_pnl = 0.0

    def on_entry_filled(self) -> None:
        self.trades_today += 1

    def on_trade_closed(self, trade: Trade) -> None:
        self.day_pnl += trade.net_pnl
        if trade.net_pnl < 0:
            self.consecutive_losses += 1
        elif trade.net_pnl > 0:
            self.consecutive_losses = 0

    # -- gates -------------------------------------------------------------

    def can_trade(self, equity: float) -> RiskDecision:
        cfg = self.config
        if cfg.min_equity and equity < cfg.min_equity:
            return RiskDecision(False, f"equity {equity:.2f} below floor {cfg.min_equity:.2f}")
        if self.trades_today >= cfg.max_trades_per_day:
            return RiskDecision(False, f"daily trade cap reached ({cfg.max_trades_per_day})")
        if self.consecutive_losses >= cfg.max_consecutive_losses:
            return RiskDecision(False, f"{self.consecutive_losses} consecutive losses")
        if cfg.daily_loss_limit_pct > 0 and self.day_start_equity > 0:
            limit = -self.day_start_equity * cfg.daily_loss_limit_pct / 100.0
            if self.day_pnl <= limit:
                return RiskDecision(False, f"daily loss limit hit ({self.day_pnl:.2f})")
        if cfg.daily_profit_target_pct > 0 and self.day_start_equity > 0:
            target = self.day_start_equity * cfg.daily_profit_target_pct / 100.0
            if self.day_pnl >= target:
                return RiskDecision(False, f"daily profit target hit ({self.day_pnl:.2f})")
        return RiskDecision(True)

    # -- sizing ------------------------------------------------------------

    def position_size(self, equity: float, risk_points: float) -> float:
        """
        Units to trade so that a stop-out costs `risk_per_trade_pct` of equity.

        Returns 0.0 when the smallest tradable size would risk more than the
        budget — refusing the trade is the correct outcome, not rounding up.
        """
        if equity <= 0 or risk_points <= 0:
            return 0.0
        risk_budget = equity * self.config.risk_per_trade_pct / 100.0
        risk_per_unit = risk_points * self.instrument.point_value
        if risk_per_unit <= 0:
            return 0.0
        raw_qty = risk_budget / risk_per_unit
        if self.config.max_units > 0:
            raw_qty = min(raw_qty, self.config.max_units)
        return self.instrument.round_qty(raw_qty)

    def risk_amount(self, qty: float, risk_points: float) -> float:
        """Monetary risk of a position, excluding commissions."""
        return self.instrument.money(risk_points, qty)
