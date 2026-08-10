"""
Performance analytics for a set of closed trades.

With a 1:1 payoff there is one number that matters more than any other: the
hit rate needed to break even after costs. `breakeven_hit_rate()` computes it,
and `PerformanceReport.edge_pct` shows how far the realised hit rate sits above
(or below) that line.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Sequence

from src.trading.models import Trade

TRADING_DAYS_PER_YEAR = 252


def breakeven_hit_rate(reward_risk_ratio: float, cost_r: float = 0.0) -> float:
    """
    Win rate (0-1) required to break even.

    `cost_r` is the average round-trip cost expressed in units of risk. For a
    1:1 strategy with zero costs the answer is 50%; every basis point of cost
    pushes the requirement above that, which is the whole difficulty of the
    approach.
    """
    if reward_risk_ratio <= 0:
        raise ValueError("reward_risk_ratio must be positive")
    return (1.0 + cost_r) / (1.0 + reward_risk_ratio)


@dataclass
class PerformanceReport:
    trades: int = 0
    wins: int = 0
    losses: int = 0
    scratches: int = 0
    win_rate_pct: float = 0.0
    gross_pnl: float = 0.0
    commission: float = 0.0
    friction: float = 0.0
    net_pnl: float = 0.0
    return_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    expectancy_r: float = 0.0
    total_r: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    longest_loss_streak: int = 0
    avg_reward_risk: float = 0.0
    cost_r: float = 0.0
    required_hit_rate_pct: float = 0.0
    edge_pct: float = 0.0
    sharpe: float = 0.0
    trading_days: int = 0
    trades_per_day: float = 0.0
    exit_reasons: dict[str, int] = field(default_factory=dict)
    starting_equity: float = 0.0
    ending_equity: float = 0.0

    def summary(self) -> str:
        lines = [
            f"Trades              {self.trades} over {self.trading_days} sessions "
            f"({self.trades_per_day:.2f}/day)",
            f"Win rate            {self.win_rate_pct:.1f}%  "
            f"(needs {self.required_hit_rate_pct:.1f}% to break even after costs)",
            f"Edge                {self.edge_pct:+.1f} pp",
            f"Net P&L             {self.net_pnl:+,.2f}  "
            f"(gross {self.gross_pnl:+,.2f}, commissions {self.commission:,.2f})",
            f"Execution friction  {self.friction:,.2f} "
            f"(commissions + slippage) = {self.cost_r:.3f}R per trade",
            f"Return              {self.return_pct:+.2f}%  "
            f"({self.starting_equity:,.2f} -> {self.ending_equity:,.2f})",
            f"Expectancy          {self.expectancy:+,.2f} per trade "
            f"({self.expectancy_r:+.3f}R), total {self.total_r:+.2f}R",
            f"Profit factor       {self.profit_factor:.2f}",
            f"Max drawdown        {self.max_drawdown:,.2f} ({self.max_drawdown_pct:.2f}%)",
            f"Longest loss streak {self.longest_loss_streak}",
            f"Avg R:R realised    {self.avg_reward_risk:.2f}",
            f"Sharpe (daily, ann) {self.sharpe:.2f}",
            "Exits               "
            + ", ".join(f"{k}={v}" for k, v in sorted(self.exit_reasons.items())),
        ]
        return "\n".join(lines)


def analyse(
    trades: Sequence[Trade],
    starting_equity: float,
    reward_risk_ratio: float = 1.0,
) -> PerformanceReport:
    """Build a full report from closed trades and the starting equity."""
    report = PerformanceReport(
        starting_equity=starting_equity,
        ending_equity=starting_equity,
        avg_reward_risk=reward_risk_ratio,
    )
    report.required_hit_rate_pct = breakeven_hit_rate(reward_risk_ratio) * 100
    if not trades:
        return report

    wins = [t for t in trades if t.net_pnl > 0]
    losses = [t for t in trades if t.net_pnl < 0]

    report.trades = len(trades)
    report.wins = len(wins)
    report.losses = len(losses)
    report.scratches = len(trades) - len(wins) - len(losses)
    report.win_rate_pct = 100.0 * len(wins) / len(trades)
    report.gross_pnl = sum(t.gross_pnl for t in trades)
    report.commission = sum(t.commission for t in trades)
    report.net_pnl = sum(t.net_pnl for t in trades)
    report.ending_equity = starting_equity + report.net_pnl
    report.return_pct = 100.0 * report.net_pnl / starting_equity if starting_equity else 0.0
    report.avg_win = sum(t.net_pnl for t in wins) / len(wins) if wins else 0.0
    report.avg_loss = sum(t.net_pnl for t in losses) / len(losses) if losses else 0.0
    report.expectancy = report.net_pnl / len(trades)
    report.total_r = sum(t.r_multiple for t in trades)
    report.expectancy_r = report.total_r / len(trades)

    gross_win = sum(t.net_pnl for t in wins)
    gross_loss = abs(sum(t.net_pnl for t in losses))
    report.profit_factor = gross_win / gross_loss if gross_loss else math.inf

    report.friction = sum(t.friction for t in trades)
    risk_money = sum(t.planned_risk_money for t in trades)
    report.cost_r = report.friction / risk_money if risk_money else 0.0
    report.required_hit_rate_pct = (
        breakeven_hit_rate(reward_risk_ratio, report.cost_r) * 100
    )
    report.edge_pct = report.win_rate_pct - report.required_hit_rate_pct

    realised_rr = [
        abs(t.exit_price - t.entry_price) / t.planned_risk_points
        for t in trades
        if t.planned_risk_points
    ]
    if realised_rr:
        report.avg_reward_risk = sum(realised_rr) / len(realised_rr)

    report.longest_loss_streak = _longest_loss_streak(trades)
    report.exit_reasons = dict(Counter(t.exit_reason.value for t in trades))

    equity_curve = build_equity_curve(trades, starting_equity)
    report.max_drawdown, report.max_drawdown_pct = max_drawdown(equity_curve)

    daily = daily_pnl(trades)
    report.trading_days = len(daily)
    report.trades_per_day = len(trades) / len(daily) if daily else 0.0
    report.sharpe = sharpe_ratio(list(daily.values()), starting_equity)
    return report


def _longest_loss_streak(trades: Sequence[Trade]) -> int:
    longest = 0
    current = 0
    for trade in trades:
        if trade.net_pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def build_equity_curve(
    trades: Sequence[Trade], starting_equity: float
) -> list[float]:
    """Equity after each closed trade, starting from the initial balance."""
    equity = starting_equity
    curve = [equity]
    for trade in trades:
        equity += trade.net_pnl
        curve.append(equity)
    return curve


def max_drawdown(curve: Sequence[float]) -> tuple[float, float]:
    """Largest peak-to-trough decline, in currency and in percent of the peak."""
    peak = -math.inf
    worst = 0.0
    worst_pct = 0.0
    for value in curve:
        peak = max(peak, value)
        drop = peak - value
        if drop > worst:
            worst = drop
            worst_pct = 100.0 * drop / peak if peak else 0.0
    return worst, worst_pct


def daily_pnl(trades: Sequence[Trade]) -> dict[date, float]:
    """Net P&L per session, keyed by the exit date."""
    out: dict[date, float] = {}
    for trade in trades:
        day = trade.exit_time.date()
        out[day] = out.get(day, 0.0) + trade.net_pnl
    return out


def sharpe_ratio(
    daily_pnls: Sequence[float],
    equity: float,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Annualised Sharpe of daily P&L, using a 0% risk-free rate."""
    if len(daily_pnls) < 2 or equity <= 0:
        return 0.0
    returns = [pnl / equity for pnl in daily_pnls]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return mean / std * math.sqrt(periods_per_year)


def hit_rate_confidence_interval(
    wins: int, trades: int, z: float = 1.96
) -> tuple[float, float]:
    """
    Wald interval around the observed hit rate.

    Included because a 1:1 strategy stands or falls on its hit rate: with 40
    trades the interval is roughly +/-15pp, which is wider than any edge worth
    trading. Use it before believing a backtest.
    """
    if trades <= 0:
        return (0.0, 0.0)
    p = wins / trades
    margin = z * math.sqrt(p * (1 - p) / trades)
    return (max(0.0, p - margin), min(1.0, p + margin))


def optimal_f_note(report: PerformanceReport) -> Optional[str]:
    """A blunt warning when the sample is too small to conclude anything."""
    if report.trades < 100:
        return (
            f"Only {report.trades} trades: the hit rate is not statistically "
            "distinguishable from a coin flip. Do not size up on this sample."
        )
    return None
