"""
§25, §43, §44 — Historical Regime Analysis and Valuation.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class MarketRegime(Enum):
    HIGH_INFLATION = "high_inflation"
    LOW_INFLATION = "low_inflation"
    RISING_RATES = "rising_rates"
    FALLING_RATES = "falling_rates"
    STRONG_GROWTH = "strong_growth"
    RECESSION = "recession"
    FINANCIAL_CRISIS = "financial_crisis"
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"


@dataclass
class RegimePerformance:
    regime: MarketRegime
    annualized_return: float
    max_drawdown: float
    volatility: float
    duration_months: int


@dataclass
class ValuationMetrics:
    """§43, §44 — Valuation for expected return adjustment."""
    pe_ratio: float | None = None
    forward_pe: float | None = None
    cape_shiller: float | None = None
    price_to_book: float | None = None
    earnings_yield: float | None = None
    dividend_yield: float | None = None

    @property
    def valuation_signal(self) -> str:
        if self.cape_shiller is None:
            return "NEUTRAL"
        if self.cape_shiller > 30:
            return "EXPENSIVE"
        if self.cape_shiller > 22:
            return "ABOVE_AVERAGE"
        if self.cape_shiller > 15:
            return "FAIR"
        if self.cape_shiller > 10:
            return "CHEAP"
        return "VERY_CHEAP"

    def expected_return_adjustment(self) -> float:
        """§44 — Adjust expected returns based on starting valuation."""
        if self.cape_shiller is None:
            return 0.0
        median_cape = 17.0
        deviation = (self.cape_shiller - median_cape) / median_cape
        return round(-deviation * 0.02, 4)
