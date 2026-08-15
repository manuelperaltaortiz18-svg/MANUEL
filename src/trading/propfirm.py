"""
Monte Carlo evaluator for prop-firm challenges.

A 1:1 strategy is fully described by three numbers: hit rate, cost in R, and
risk per trade. Everything else — profit target, daily loss limit, trailing
drawdown — is arithmetic on top. This module runs that arithmetic thousands of
times so a target return can be answered with a probability instead of a hope.

The point it exists to make: in a funded-account challenge the binding
constraint is the drawdown limit, not the profit target. Sizing up to chase a
large return raises the chance of breaching the limit far faster than it raises
the chance of passing.
"""
from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChallengeRules:
    """
    Typical funded-account evaluation. Defaults follow the common 10/5/10 shape.

    `trailing_drawdown` models the stricter firms, where the limit follows the
    account's high-water mark instead of the starting balance.
    """

    profit_target_pct: float = 10.0
    daily_loss_pct: float = 5.0
    max_drawdown_pct: float = 10.0
    trailing_drawdown: bool = True
    max_days: int = 30


@dataclass(frozen=True)
class StrategyStats:
    """What the strategy does per trade, in units of risk."""

    hit_rate: float
    reward_risk: float = 1.0
    cost_r: float = 0.0  # friction per trade, in R
    trades_per_day: float = 2.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.hit_rate <= 1.0:
            raise ValueError("hit_rate must be a probability")
        if self.reward_risk <= 0:
            raise ValueError("reward_risk must be positive")

    @property
    def win_r(self) -> float:
        return self.reward_risk - self.cost_r

    @property
    def loss_r(self) -> float:
        return -(1.0 + self.cost_r)

    @property
    def expectancy_r(self) -> float:
        return self.hit_rate * self.win_r + (1 - self.hit_rate) * self.loss_r

    @property
    def breakeven_hit_rate(self) -> float:
        return (1.0 + self.cost_r) / (1.0 + self.reward_risk)


@dataclass
class ChallengeOutcome:
    passed: int = 0
    failed_daily: int = 0
    failed_drawdown: int = 0
    ran_out_of_time: int = 0
    trials: int = 0
    median_return_pct: float = 0.0
    median_days_to_pass: float = 0.0
    worst_drawdown_pct: float = 0.0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.trials if self.trials else 0.0

    @property
    def failure_rate(self) -> float:
        return (self.failed_daily + self.failed_drawdown) / self.trials if self.trials else 0.0

    def summary(self) -> str:
        return (
            f"pasa {self.pass_rate * 100:5.1f}%   "
            f"revienta {self.failure_rate * 100:5.1f}% "
            f"(diario {self.failed_daily / self.trials * 100:.1f}%, "
            f"DD {self.failed_drawdown / self.trials * 100:.1f}%)   "
            f"sin tiempo {self.ran_out_of_time / self.trials * 100:5.1f}%"
        )


def simulate_challenge(
    stats: StrategyStats,
    risk_per_trade_pct: float,
    rules: ChallengeRules = ChallengeRules(),
    trials: int = 20_000,
    seed: int = 7,
) -> ChallengeOutcome:
    """
    Run the evaluation `trials` times and count how it ends.

    Each trade moves equity by `risk_per_trade_pct` of *current* equity times
    the trade's R outcome, so position size compounds the way the bot's own
    sizing does.
    """
    rng = random.Random(seed)
    outcome = ChallengeOutcome(trials=trials)
    returns: list[float] = []
    days_to_pass: list[int] = []
    worst_dd = 0.0
    risk = risk_per_trade_pct / 100.0
    trades_per_day = max(1, round(stats.trades_per_day))

    for _ in range(trials):
        equity = 1.0
        peak = 1.0
        finished = False

        for day in range(1, rules.max_days + 1):
            day_start = equity
            for _ in range(trades_per_day):
                r = stats.win_r if rng.random() < stats.hit_rate else stats.loss_r
                equity *= 1.0 + risk * r
                peak = max(peak, equity)

                floor = peak if rules.trailing_drawdown else 1.0
                worst_dd = max(worst_dd, (peak - equity) / peak)

                if equity <= floor * (1.0 - rules.max_drawdown_pct / 100.0):
                    outcome.failed_drawdown += 1
                    finished = True
                    break
                if equity >= 1.0 + rules.profit_target_pct / 100.0:
                    outcome.passed += 1
                    days_to_pass.append(day)
                    finished = True
                    break
                if equity <= day_start * (1.0 - rules.daily_loss_pct / 100.0):
                    outcome.failed_daily += 1
                    finished = True
                    break
            if finished:
                break

        if not finished:
            outcome.ran_out_of_time += 1
        returns.append((equity - 1.0) * 100.0)

    outcome.median_return_pct = statistics.median(returns)
    outcome.median_days_to_pass = statistics.median(days_to_pass) if days_to_pass else 0.0
    outcome.worst_drawdown_pct = worst_dd * 100.0
    return outcome


def probability_of_return(
    stats: StrategyStats,
    risk_per_trade_pct: float,
    target_return_pct: float,
    trading_days: int = 250,
    ruin_drawdown_pct: float = 50.0,
    trials: int = 20_000,
    seed: int = 11,
) -> tuple[float, float]:
    """
    Chance of reaching a target return within `trading_days`, and of ruin first.

    Use this to price a headline number like "70% a year" honestly: it returns
    the probability of getting there and the probability of losing half the
    account on the way.
    """
    rng = random.Random(seed)
    risk = risk_per_trade_pct / 100.0
    trades_per_day = max(1, round(stats.trades_per_day))
    hits = 0
    ruined = 0

    for _ in range(trials):
        equity = 1.0
        peak = 1.0
        for _ in range(trading_days * trades_per_day):
            r = stats.win_r if rng.random() < stats.hit_rate else stats.loss_r
            equity *= 1.0 + risk * r
            peak = max(peak, equity)
            if equity <= peak * (1.0 - ruin_drawdown_pct / 100.0):
                ruined += 1
                break
            if equity >= 1.0 + target_return_pct / 100.0:
                hits += 1
                break

    return hits / trials, ruined / trials


def required_hit_rate_for_return(
    target_return_pct: float,
    risk_per_trade_pct: float,
    trades: int,
    reward_risk: float = 1.0,
    cost_r: float = 0.0,
) -> Optional[float]:
    """
    Hit rate whose *expected* path reaches the target. None if impossible.

    This is the optimistic bound — half of all outcomes land below it — so treat
    it as the floor of what the strategy must achieve, never as a forecast.
    """
    if trades <= 0 or risk_per_trade_pct <= 0:
        raise ValueError("trades and risk must be positive")

    growth = (1.0 + target_return_pct / 100.0) ** (1.0 / trades) - 1.0
    needed_r = growth / (risk_per_trade_pct / 100.0)
    win_r = reward_risk - cost_r
    loss_r = -(1.0 + cost_r)
    # needed_r = p * win_r + (1 - p) * loss_r
    denominator = win_r - loss_r
    if denominator <= 0:
        return None
    p = (needed_r - loss_r) / denominator
    return p if 0.0 <= p <= 1.0 else None


@dataclass
class YearOutcome:
    """Distribution of a year's result, not a single number."""

    median_return_pct: float = 0.0
    p10_return_pct: float = 0.0
    p90_return_pct: float = 0.0
    median_max_dd_pct: float = 0.0
    worst_max_dd_pct: float = 0.0
    prob_target_pct: float = 0.0
    prob_loss_pct: float = 0.0
    trades: int = 0

    def summary(self) -> str:
        return (
            f"mediana {self.median_return_pct:+.1f}%  "
            f"(p10 {self.p10_return_pct:+.1f}% / p90 {self.p90_return_pct:+.1f}%)  "
            f"DD mediano {self.median_max_dd_pct:.1f}%  "
            f"P(objetivo) {self.prob_target_pct:.0f}%  "
            f"P(pérdida) {self.prob_loss_pct:.0f}%"
        )


def simulate_year(
    stats: StrategyStats,
    risk_per_trade_pct: float,
    sessions: int = 250,
    target_return_pct: float = 70.0,
    trials: int = 5_000,
    seed: int = 13,
) -> YearOutcome:
    """
    Percentiles of a year's outcome for a given edge and position size.

    A single expected return is a misleading answer: the same edge produces a
    wide band of results, and the drawdown along the way is what decides
    whether an account survives to collect the average.
    """
    rng = random.Random(seed)
    risk = risk_per_trade_pct / 100.0
    trades = max(1, round(stats.trades_per_day)) * sessions
    returns: list[float] = []
    drawdowns: list[float] = []
    hits = 0
    losses = 0

    for _ in range(trials):
        equity = 1.0
        peak = 1.0
        worst = 0.0
        reached = False
        for _ in range(trades):
            r = stats.win_r if rng.random() < stats.hit_rate else stats.loss_r
            equity = max(1e-9, equity * (1.0 + risk * r))
            peak = max(peak, equity)
            worst = max(worst, (peak - equity) / peak)
            if equity >= 1.0 + target_return_pct / 100.0:
                reached = True
        returns.append((equity - 1.0) * 100.0)
        drawdowns.append(worst * 100.0)
        hits += 1 if reached else 0
        losses += 1 if equity < 1.0 else 0

    returns.sort()
    drawdowns.sort()

    def pct(values, q):
        return values[min(len(values) - 1, int(q * len(values)))]

    return YearOutcome(
        median_return_pct=statistics.median(returns),
        p10_return_pct=pct(returns, 0.10),
        p90_return_pct=pct(returns, 0.90),
        median_max_dd_pct=statistics.median(drawdowns),
        worst_max_dd_pct=drawdowns[-1],
        prob_target_pct=100.0 * hits / trials,
        prob_loss_pct=100.0 * losses / trials,
        trades=trades,
    )


def trades_needed_to_detect(
    hit_rate: float, breakeven: float, z: float = 1.96
) -> Optional[int]:
    """
    Trades required before a hit rate can be told apart from break-even.

    Below this count a backtest cannot distinguish an edge from luck, so tuning
    parameters on it is fitting noise. Returns None when the two rates are
    equal — no sample size can separate them.
    """
    if not 0.0 < hit_rate < 1.0 or not 0.0 < breakeven < 1.0:
        raise ValueError("Both rates must be probabilities")
    gap = abs(hit_rate - breakeven)
    if gap < 1e-9:
        return None
    variance = hit_rate * (1.0 - hit_rate)
    return int(math.ceil((z ** 2) * variance / (gap ** 2)))
