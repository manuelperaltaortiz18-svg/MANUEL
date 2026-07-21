"""
§4, §8, §9, §14, §19, §21, §38, §39, §48, §50, §51, §52, §60 —
All scoring systems for the long-term investment framework.
"""
from __future__ import annotations
from dataclasses import dataclass
from src.config.constants import (
    DECISION_HIERARCHY_WEIGHTS,
    STRATEGIC_HIGH_THRESHOLD,
    TACTICAL_HIGH_THRESHOLD,
)


@dataclass
class CompoundingScore:
    """§4 — Long-Term Compounding Score (0–100)."""
    historical_cagr: float = 0
    real_returns: float = 0
    drawdown_quality: float = 0
    recovery_speed: float = 0
    volatility: float = 0
    consistency: float = 0
    diversification: float = 0
    cost_efficiency: float = 0
    tracking_quality: float = 0
    structural_growth: float = 0
    survivability: float = 0
    liquidity: float = 0
    fund_size: float = 0
    replication_quality: float = 0
    index_methodology: float = 0
    historical_resilience: float = 0
    risk_adjusted_return: float = 0

    @property
    def total(self) -> float:
        weights = {
            "historical_cagr": 0.12,
            "real_returns": 0.08,
            "drawdown_quality": 0.06,
            "recovery_speed": 0.06,
            "volatility": 0.05,
            "consistency": 0.10,
            "diversification": 0.08,
            "cost_efficiency": 0.10,
            "tracking_quality": 0.04,
            "structural_growth": 0.06,
            "survivability": 0.05,
            "liquidity": 0.04,
            "fund_size": 0.03,
            "replication_quality": 0.03,
            "index_methodology": 0.03,
            "historical_resilience": 0.04,
            "risk_adjusted_return": 0.03,
        }
        return round(sum(getattr(self, k) * v for k, v in weights.items()), 1)


@dataclass
class ConsistencyScore:
    """§8 — Long-Term Consistency Score (0–100)."""
    pct_positive_rolling_5y: float = 0
    pct_positive_rolling_10y: float = 0
    median_rolling_cagr: float = 0
    return_dispersion: float = 0
    drawdown_frequency: float = 0
    recovery_speed: float = 0

    @property
    def total(self) -> float:
        components = [
            self.pct_positive_rolling_5y * 0.20,
            self.pct_positive_rolling_10y * 0.25,
            self.median_rolling_cagr * 0.20,
            self.return_dispersion * 0.15,
            self.drawdown_frequency * 0.10,
            self.recovery_speed * 0.10,
        ]
        return round(sum(components), 1)


@dataclass
class ResilienceScore:
    """§9 — Historical Resilience Score (0–100)."""
    dotcom: float = 0
    gfc: float = 0
    eurozone: float = 0
    covid: float = 0
    inflation_2022: float = 0

    @property
    def total(self) -> float:
        weights = [0.20, 0.30, 0.10, 0.20, 0.20]
        values = [self.dotcom, self.gfc, self.eurozone, self.covid, self.inflation_2022]
        return round(sum(v * w for v, w in zip(values, weights)), 1)


@dataclass
class AlphaPersistence:
    """§14 — Alpha persistence metrics."""
    rolling_alpha_3y: float | None = None
    rolling_alpha_5y: float | None = None
    rolling_alpha_10y: float | None = None
    consistency_vs_benchmark: float = 0
    downside_capture: float = 100
    upside_capture: float = 100

    @property
    def is_persistent(self) -> bool:
        if self.rolling_alpha_5y is None:
            return False
        return (
            self.rolling_alpha_5y > 0.005
            and self.consistency_vs_benchmark > 60
            and self.downside_capture < 95
        )


@dataclass
class TimingDependencyScore:
    """§19 — How much a strategy depends on market timing (0–100, lower is better)."""
    entry_sensitivity: float = 0
    exit_sensitivity: float = 0
    cash_exposure_avg: float = 0
    turnover_rate: float = 0
    signal_frequency: float = 0

    @property
    def total(self) -> float:
        return round(
            self.entry_sensitivity * 0.25
            + self.exit_sensitivity * 0.25
            + self.cash_exposure_avg * 0.20
            + self.turnover_rate * 0.15
            + self.signal_frequency * 0.15,
            1,
        )


@dataclass
class CompoundingInterruptionRisk:
    """§21 — Risk that tactical decisions erode compounding (0–100, lower is better)."""
    excessive_turnover: float = 0
    market_timing: float = 0
    cash_exposure: float = 0
    tax_realization: float = 0
    transaction_costs: float = 0
    missed_rebounds: float = 0

    @property
    def total(self) -> float:
        return round(
            sum([
                self.excessive_turnover * 0.20,
                self.market_timing * 0.20,
                self.cash_exposure * 0.15,
                self.tax_realization * 0.20,
                self.transaction_costs * 0.10,
                self.missed_rebounds * 0.15,
            ]),
            1,
        )


@dataclass
class QualityOfCompounding:
    """§48 — Quality of Compounding Score (0–100)."""
    cagr_quality: float = 0
    volatility_adj: float = 0
    permanent_loss_risk: float = 0
    recovery_speed: float = 0
    earnings_consistency: float = 0
    cost_efficiency: float = 0
    diversification: float = 0

    @property
    def total(self) -> float:
        return round(
            self.cagr_quality * 0.20
            + self.volatility_adj * 0.15
            + self.permanent_loss_risk * 0.15
            + self.recovery_speed * 0.15
            + self.earnings_consistency * 0.10
            + self.cost_efficiency * 0.15
            + self.diversification * 0.10,
            1,
        )


@dataclass
class LongTermFailureRisk:
    """§50 — Structural failure risk assessment (0–100, lower is better)."""
    closure_risk: float = 0
    low_aum: float = 0
    narrow_theme: float = 0
    structural_disruption: float = 0
    high_fees: float = 0
    poor_index: float = 0
    concentration: float = 0
    counterparty: float = 0
    replication: float = 0

    @property
    def total(self) -> float:
        values = [
            self.closure_risk, self.low_aum, self.narrow_theme,
            self.structural_disruption, self.high_fees, self.poor_index,
            self.concentration, self.counterparty, self.replication,
        ]
        return round(sum(values) / len(values), 1)


@dataclass
class PortfolioComplexity:
    """§51 — Portfolio Complexity Score (0–100, lower is better)."""
    position_count: float = 0
    overlap_degree: float = 0
    rebalancing_difficulty: float = 0
    monitoring_burden: float = 0

    @property
    def total(self) -> float:
        return round(
            self.position_count * 0.30
            + self.overlap_degree * 0.30
            + self.rebalancing_difficulty * 0.20
            + self.monitoring_burden * 0.20,
            1,
        )


@dataclass
class BehavioralRisk:
    """§52 — Behavioral risk of a strategy (0–100, lower is better)."""
    trading_temptation: float = 0
    panic_sell_risk: float = 0
    complexity_confusion: float = 0
    performance_chasing: float = 0

    @property
    def total(self) -> float:
        return round(
            self.trading_temptation * 0.25
            + self.panic_sell_risk * 0.30
            + self.complexity_confusion * 0.20
            + self.performance_chasing * 0.25,
            1,
        )


@dataclass
class RotationAlpha:
    """§60 — Value added by rotation vs buy-and-hold."""
    cagr_difference: float = 0
    sharpe_difference: float = 0
    max_dd_difference: float = 0
    tax_adjusted_cagr_diff: float = 0
    annual_turnover: float = 0
    missed_best_days: int = 0
    avg_holding_period_months: float = 0

    @property
    def adds_value(self) -> bool:
        return (
            self.cagr_difference > 0.005
            and self.sharpe_difference > 0.05
            and self.tax_adjusted_cagr_diff > 0
        )


@dataclass
class StrategicScore:
    """§39 — Is this asset a good long-term vehicle? (0–100)"""
    compounding_score: float = 0
    consistency_score: float = 0
    resilience_score: float = 0
    cost_efficiency: float = 0
    diversification: float = 0
    failure_risk_inv: float = 0  # inverted: 100 = low risk

    @property
    def total(self) -> float:
        return round(
            self.compounding_score * 0.25
            + self.consistency_score * 0.20
            + self.resilience_score * 0.15
            + self.cost_efficiency * 0.15
            + self.diversification * 0.15
            + self.failure_risk_inv * 0.10,
            1,
        )


@dataclass
class TacticalScore:
    """§39 — Is this asset attractive now? (0–100)"""
    momentum_1m: float = 0
    momentum_3m: float = 0
    momentum_6m: float = 0
    relative_strength: float = 0
    trend: float = 0
    regime_fit: float = 0
    valuation: float = 0

    @property
    def total(self) -> float:
        return round(
            self.momentum_1m * 0.05
            + self.momentum_3m * 0.10
            + self.momentum_6m * 0.15
            + self.relative_strength * 0.20
            + self.trend * 0.20
            + self.regime_fit * 0.15
            + self.valuation * 0.15,
            1,
        )


def strategic_tactical_matrix(
    strategic: float,
    tactical: float,
) -> str:
    """§40 — Decision matrix."""
    s_high = strategic >= STRATEGIC_HIGH_THRESHOLD
    t_high = tactical >= TACTICAL_HIGH_THRESHOLD

    if s_high and t_high:
        return "STRONG CORE / CONSIDER INCREASE"
    if s_high and not t_high:
        return "CORE HOLD / POSSIBLE TEMPORARY UNDERWEIGHT"
    if not s_high and t_high:
        return "SATELLITE TACTICAL OPPORTUNITY"
    return "AVOID / EXIT CANDIDATE"


@dataclass
class LongTermPortfolioScore:
    """§38 — Portfolio-level score (0–100)."""
    compounding_potential: float = 0
    diversification: float = 0
    cost_efficiency: float = 0
    historical_resilience: float = 0
    risk_adjusted_return: float = 0
    drawdown_sustainability: float = 0
    tax_efficiency: float = 0
    structural_growth: float = 0
    simplicity: float = 0
    turnover_efficiency: float = 0

    @property
    def total(self) -> float:
        weights = [0.15, 0.12, 0.12, 0.10, 0.10, 0.10, 0.08, 0.08, 0.08, 0.07]
        values = [
            self.compounding_potential, self.diversification, self.cost_efficiency,
            self.historical_resilience, self.risk_adjusted_return,
            self.drawdown_sustainability, self.tax_efficiency, self.structural_growth,
            self.simplicity, self.turnover_efficiency,
        ]
        return round(sum(v * w for v, w in zip(values, weights)), 1)
