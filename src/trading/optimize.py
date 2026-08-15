"""
Parameter search with the honesty machinery attached.

Optimising a strategy on its own backtest is the easiest way to build something
that worked yesterday and never again. Two guards are built in rather than
offered as options:

* **Walk-forward split.** Every candidate is scored on data it was not tuned
  on. The in-sample number is reported next to the out-of-sample one, so the
  gap between them is impossible to miss.
* **A chance benchmark.** Testing N parameter sets and keeping the best is
  N chances to get lucky. `best_of_n_by_chance` measures what the luckiest of N
  coin-flippers would have shown on the same number of trades. A result that
  fails to beat that has found nothing.
"""
from __future__ import annotations

import itertools
import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Optional, Sequence

from src.trading.metrics import PerformanceReport
from src.trading.models import Bar


def iter_param_sets(grid: dict[str, Sequence[Any]]) -> Iterator[dict[str, Any]]:
    """Every combination in the grid, as keyword dicts."""
    if not grid:
        yield {}
        return
    names = list(grid)
    for values in itertools.product(*(grid[name] for name in names)):
        yield dict(zip(names, values))


def grid_size(grid: dict[str, Sequence[Any]]) -> int:
    total = 1
    for values in grid.values():
        total *= max(1, len(values))
    return total


def split_by_session(
    bars: Sequence[Bar], in_sample_fraction: float = 0.6
) -> tuple[list[Bar], list[Bar]]:
    """
    Chronological split on a session boundary.

    Splitting mid-session would leak: the opening range of a day would be tuned
    on one side and traded on the other.
    """
    if not 0.0 < in_sample_fraction < 1.0:
        raise ValueError("in_sample_fraction must be between 0 and 1")
    days = sorted({bar.timestamp.date() for bar in bars})
    if len(days) < 2:
        raise ValueError("Need at least two sessions to split")
    cutoff_index = max(1, min(len(days) - 1, round(len(days) * in_sample_fraction)))
    cutoff = days[cutoff_index]
    in_sample = [b for b in bars if b.timestamp.date() < cutoff]
    out_sample = [b for b in bars if b.timestamp.date() >= cutoff]
    return in_sample, out_sample


@dataclass
class Candidate:
    params: dict[str, Any]
    in_sample: PerformanceReport
    out_sample: Optional[PerformanceReport] = None

    @property
    def in_sample_score(self) -> float:
        return self.in_sample.expectancy_r

    @property
    def out_sample_score(self) -> float:
        return self.out_sample.expectancy_r if self.out_sample else 0.0

    @property
    def degradation(self) -> float:
        """How much of the in-sample edge survived. Negative means it reversed."""
        return self.out_sample_score - self.in_sample_score

    def describe(self) -> str:
        bits = ", ".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return bits or "(defaults)"


@dataclass
class OptimizationOutcome:
    candidates: list[Candidate] = field(default_factory=list)
    combinations_tested: int = 0
    in_sample_sessions: int = 0
    out_sample_sessions: int = 0
    chance_hit_rate: float = 0.0
    chance_expectancy_r: float = 0.0

    @property
    def best(self) -> Optional[Candidate]:
        return self.candidates[0] if self.candidates else None

    def verdict(self) -> str:
        """A plain reading of whether the search found anything real."""
        best = self.best
        if best is None:
            return "No candidate produced enough trades to judge."
        if best.out_sample is None:
            return "No out-of-sample data: this result is untested."
        if best.out_sample.trades < 30:
            return (
                f"Only {best.out_sample.trades} out-of-sample trades — too few to "
                "confirm or reject anything."
            )
        if best.out_sample_score <= 0:
            return (
                "The best in-sample setting loses out-of-sample. That is what "
                "overfitting looks like; do not trade it."
            )
        if best.in_sample.win_rate_pct <= self.chance_hit_rate * 100:
            return (
                f"The best hit rate ({best.in_sample.win_rate_pct:.1f}%) is no better "
                f"than the luckiest of {self.combinations_tested} coin-flippers would "
                f"show ({self.chance_hit_rate * 100:.1f}%). The search found noise."
            )
        return (
            f"Survives out-of-sample at {best.out_sample_score:+.3f}R per trade. "
            "Necessary, not sufficient: confirm on a third period before sizing up."
        )


def optimise(
    bars: Sequence[Bar],
    grid: dict[str, Sequence[Any]],
    evaluate: Callable[[Sequence[Bar], dict[str, Any]], PerformanceReport],
    in_sample_fraction: float = 0.6,
    min_trades: int = 20,
    top: int = 10,
    seed: int = 5,
    reward_risk: float = 1.0,
) -> OptimizationOutcome:
    """
    Score every parameter set in-sample, then re-score the survivors out-of-sample.

    `evaluate` runs one backtest and returns its report; keeping it injected
    means this module never has to know which strategy is being tuned.
    """
    in_bars, out_bars = split_by_session(bars, in_sample_fraction)
    outcome = OptimizationOutcome(
        combinations_tested=grid_size(grid),
        in_sample_sessions=len({b.timestamp.date() for b in in_bars}),
        out_sample_sessions=len({b.timestamp.date() for b in out_bars}),
    )

    scored: list[Candidate] = []
    for params in iter_param_sets(grid):
        report = evaluate(in_bars, params)
        if report.trades < min_trades:
            continue
        scored.append(Candidate(params=params, in_sample=report))

    scored.sort(key=lambda c: c.in_sample_score, reverse=True)
    survivors = scored[:top]
    for candidate in survivors:
        candidate.out_sample = evaluate(out_bars, candidate.params)

    outcome.candidates = survivors
    if survivors:
        trades = survivors[0].in_sample.trades
        # El nulo depende del pago: 50 % en 1:1, 33 % en 1:2.
        null_rate = 1.0 / (1.0 + reward_risk)
        outcome.chance_hit_rate = best_of_n_by_chance(
            outcome.combinations_tested, trades, seed=seed, null_rate=null_rate
        )
        outcome.chance_expectancy_r = (
            outcome.chance_hit_rate * reward_risk - (1 - outcome.chance_hit_rate)
        )
    return outcome


def best_of_n_by_chance(
    trials: int,
    trades: int,
    simulations: int = 4_000,
    seed: int = 5,
    null_rate: float = 0.5,
) -> float:
    """
    Hit rate the luckiest of `trials` edge-less strategies would post.

    This is the bar a grid search has to clear before its winner means anything:
    search hard enough and something always looks good.

    `null_rate` is the hit rate of no edge at all, which depends on the payoff:
    0.5 for a 1:1 bracket, 1/3 for 1:2, 1/(1+rr) in general. Using 0.5 for a
    1:2 strategy would compare it against the wrong coin entirely.

    Each draw uses the normal approximation to the binomial, accurate well
    below the trade counts that matter here.
    """
    if trials <= 0 or trades <= 0:
        return 0.0
    if not 0.0 < null_rate < 1.0:
        raise ValueError("null_rate must be a probability")
    rng = random.Random(seed)
    sigma = math.sqrt(null_rate * (1.0 - null_rate) / trades)
    best_rates = [
        max(rng.gauss(null_rate, sigma) for _ in range(trials))
        for _ in range(simulations)
    ]
    return min(1.0, statistics.mean(best_rates))
