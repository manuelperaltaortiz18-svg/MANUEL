"""
§2, §17, §18, §22, §37, §40, §41, §42, §62, §63, §64, §65 —
Decision engine: the heart of the long-term investment system.
"""
from __future__ import annotations
from dataclasses import dataclass
from src.scoring.scores import (
    StrategicScore,
    TacticalScore,
    strategic_tactical_matrix,
    LongTermPortfolioScore,
)
from src.config.constants import DECISION_HIERARCHY_WEIGHTS


@dataclass
class InvestmentDecision:
    ticker: str
    action: str  # HOLD, BUY, REDUCE, EXIT, INCREASE, ROTATE
    strategic_score: float
    tactical_score: float
    matrix_signal: str
    rationale: str
    long_term_impact: str
    passes_five_year_test: bool
    passes_compounding_test: bool


def evaluate_decision(
    ticker: str,
    strategic: StrategicScore,
    tactical: TacticalScore,
    current_holding: bool = True,
    is_core: bool = True,
) -> InvestmentDecision:
    """§41, §62, §63 — Full decision hierarchy evaluation."""
    s = strategic.total
    t = tactical.total
    matrix = strategic_tactical_matrix(s, t)

    five_year = s >= 70
    compounding = s >= 60 and t >= 40

    if current_holding:
        if s >= 70 and t >= 60:
            action = "HOLD / CONSIDER INCREASE"
        elif s >= 70 and t < 60:
            if is_core:
                action = "HOLD"  # §2 — tactical weakness doesn't override strategic quality
            else:
                action = "HOLD / POSSIBLE TRIM"
        elif s < 50 and t < 40:
            action = "EXIT CANDIDATE"
        elif s < 50:
            action = "REDUCE"
        else:
            action = "HOLD"
    else:
        if s >= 70 and t >= 60:
            action = "BUY CANDIDATE"
        elif s >= 70:
            action = "WATCHLIST — WAIT FOR TACTICAL ENTRY"
        elif s >= 50 and t >= 70:
            action = "SATELLITE OPPORTUNITY"
        else:
            action = "AVOID"

    # §42 — Performance chasing detection
    chasing_warning = ""
    if t >= 70 and s < 50:
        chasing_warning = " WARNING: Possible performance chasing — high tactical but low strategic quality."

    rationale = (
        f"Strategic: {s:.0f}/100, Tactical: {t:.0f}/100. "
        f"Matrix: {matrix}.{chasing_warning}"
    )

    impact = (
        f"{'Passes' if five_year else 'Fails'} 5-year hold test. "
        f"{'Supports' if compounding else 'May interrupt'} long-term compounding."
    )

    return InvestmentDecision(
        ticker=ticker,
        action=action,
        strategic_score=s,
        tactical_score=t,
        matrix_signal=matrix,
        rationale=rationale,
        long_term_impact=impact,
        passes_five_year_test=five_year,
        passes_compounding_test=compounding,
    )


@dataclass
class PortfolioReview:
    """§37, §53 — Portfolio-level review output."""
    portfolio_score: LongTermPortfolioScore
    decisions: list[InvestmentDecision]
    wealth_projection: dict[int, float]
    rebalance_needed: bool
    review_type: str  # "strategic" or "tactical"

    @property
    def summary(self) -> str:
        holds = sum(1 for d in self.decisions if "HOLD" in d.action)
        actions = sum(1 for d in self.decisions if "HOLD" not in d.action)
        return (
            f"Portfolio Score: {self.portfolio_score.total:.0f}/100. "
            f"{holds} positions to hold, {actions} requiring attention. "
            f"Rebalance {'needed' if self.rebalance_needed else 'not needed'}."
        )
