"""
§16, §20, §55, §56, §57, §59, §62, §63 — Compounding-Preserving Rotation Engine.
"""
from __future__ import annotations
from dataclasses import dataclass
from src.models.asset import AssetRole
from src.config.constants import CORE_ROTATION_PENALTY, SATELLITE_ROTATION_PENALTY


@dataclass
class RotationCost:
    """§20, §55 — Full cost of executing a rotation."""
    transaction_cost_pct: float = 0.10
    estimated_tax_pct: float = 0.0
    time_out_of_market_days: int = 1
    opportunity_cost_pct: float = 0.0
    signal_uncertainty: float = 0.0

    @property
    def total_friction(self) -> float:
        return (
            self.transaction_cost_pct
            + self.estimated_tax_pct
            + self.opportunity_cost_pct
            + self.signal_uncertainty
        )


@dataclass
class RotationProposal:
    """§57 — Compounding-adjusted replacement evaluation."""
    source_ticker: str
    target_ticker: str
    role: AssetRole
    source_strategic_score: float
    target_strategic_score: float
    source_tactical_score: float
    target_tactical_score: float
    expected_cagr_improvement: float
    cost_improvement_pct: float
    rotation_cost: RotationCost

    @property
    def raw_score_improvement(self) -> float:
        return self.target_strategic_score - self.source_strategic_score

    @property
    def penalty_multiplier(self) -> float:
        if self.role == AssetRole.CORE:
            return CORE_ROTATION_PENALTY
        return SATELLITE_ROTATION_PENALTY

    @property
    def net_benefit(self) -> float:
        """§55 — Rotation benefit minus compounding interruption cost."""
        benefit = (
            self.raw_score_improvement
            + self.expected_cagr_improvement * 100
            + self.cost_improvement_pct * 50
        )
        cost = self.rotation_cost.total_friction * self.penalty_multiplier * 10
        return benefit - cost

    @property
    def should_rotate(self) -> bool:
        """§56, §62, §63 — Minimum evidence threshold."""
        if self.role == AssetRole.CORE:
            return self.net_benefit > 15.0
        return self.net_benefit > 5.0

    @property
    def decision_rationale(self) -> str:
        if not self.should_rotate:
            return (
                f"HOLD: Net benefit ({self.net_benefit:.1f}) below "
                f"{'core' if self.role == AssetRole.CORE else 'satellite'} threshold. "
                "Compounding interruption risk outweighs expected improvement."
            )
        return (
            f"ROTATE: Net benefit ({self.net_benefit:.1f}) justifies change. "
            f"Expected CAGR improvement: {self.expected_cagr_improvement:+.2%}, "
            f"Cost improvement: {self.cost_improvement_pct:+.2%}."
        )


def five_year_hold_test(proposal: RotationProposal) -> bool:
    """§63 — Would you still recommend this if the investor couldn't touch
    the portfolio again for five years?"""
    return (
        proposal.target_strategic_score > proposal.source_strategic_score + 5
        or proposal.cost_improvement_pct > 0.30
    )


def buy_and_hold_benchmark_test(
    strategy_cagr: float,
    buyhold_cagr: float,
    strategy_sharpe: float,
    buyhold_sharpe: float,
    strategy_max_dd: float,
    buyhold_max_dd: float,
    strategy_turnover: float,
) -> dict[str, object]:
    """§59 — Compare rotation strategy against simple buy & hold."""
    cagr_diff = strategy_cagr - buyhold_cagr
    sharpe_diff = strategy_sharpe - buyhold_sharpe
    dd_diff = strategy_max_dd - buyhold_max_dd

    adds_value = (
        cagr_diff > 0
        or (cagr_diff > -0.005 and dd_diff > 0.05)
    )

    return {
        "cagr_difference": round(cagr_diff, 4),
        "sharpe_difference": round(sharpe_diff, 4),
        "max_dd_improvement": round(dd_diff, 4),
        "strategy_turnover": strategy_turnover,
        "adds_value": adds_value,
        "recommendation": "KEEP STRATEGY" if adds_value else "PREFER BUY & HOLD",
    }
