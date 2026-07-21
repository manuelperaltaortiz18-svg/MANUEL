"""
§35, §36, §54 — Strategic Asset Allocation Engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from src.config.constants import MAX_TACTICAL_DEVIATION_PP


@dataclass
class AssetClassAssumption:
    """§24 — Long-term capital market assumptions per asset class."""
    asset_class: str
    expected_nominal_return: float
    expected_real_return: float
    expected_volatility: float
    expected_correlations: dict[str, float] = field(default_factory=dict)


DEFAULT_ASSUMPTIONS: list[AssetClassAssumption] = [
    AssetClassAssumption("global_equity", 0.07, 0.05, 0.16),
    AssetClassAssumption("us_equity", 0.075, 0.055, 0.17),
    AssetClassAssumption("europe_equity", 0.065, 0.045, 0.18),
    AssetClassAssumption("em_equity", 0.08, 0.055, 0.22),
    AssetClassAssumption("global_bonds", 0.03, 0.01, 0.06),
    AssetClassAssumption("inflation_linked", 0.025, 0.005, 0.08),
    AssetClassAssumption("reits", 0.065, 0.045, 0.19),
    AssetClassAssumption("commodities", 0.04, 0.02, 0.18),
    AssetClassAssumption("cash", 0.02, 0.00, 0.01),
]


@dataclass
class AllocationTarget:
    asset_class: str
    strategic_weight_pct: float
    min_weight_pct: float
    max_weight_pct: float

    @property
    def tactical_range(self) -> tuple[float, float]:
        low = max(self.min_weight_pct, self.strategic_weight_pct - MAX_TACTICAL_DEVIATION_PP)
        high = min(self.max_weight_pct, self.strategic_weight_pct + MAX_TACTICAL_DEVIATION_PP)
        return (low, high)


@dataclass
class StrategicAllocation:
    """§35 — The reference long-term allocation."""
    name: str
    targets: list[AllocationTarget] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(t.strategic_weight_pct for t in self.targets)

    def deviation(self, actual_weights: dict[str, float]) -> dict[str, float]:
        return {
            t.asset_class: actual_weights.get(t.asset_class, 0) - t.strategic_weight_pct
            for t in self.targets
        }

    def needs_rebalance(self, actual_weights: dict[str, float], threshold_pp: float = 5.0) -> bool:
        """§54 — Check if any allocation exceeds threshold."""
        devs = self.deviation(actual_weights)
        return any(abs(d) > threshold_pp for d in devs.values())


GROWTH_ALLOCATION = StrategicAllocation(
    name="Long-Term Growth (40Y Horizon)",
    targets=[
        AllocationTarget("global_equity", 60, 45, 75),
        AllocationTarget("us_equity", 15, 5, 25),
        AllocationTarget("em_equity", 10, 0, 20),
        AllocationTarget("global_bonds", 10, 0, 25),
        AllocationTarget("reits", 5, 0, 10),
    ],
)

BALANCED_ALLOCATION = StrategicAllocation(
    name="Balanced Growth (30Y Horizon)",
    targets=[
        AllocationTarget("global_equity", 50, 35, 65),
        AllocationTarget("us_equity", 10, 0, 20),
        AllocationTarget("em_equity", 5, 0, 15),
        AllocationTarget("global_bonds", 25, 10, 40),
        AllocationTarget("inflation_linked", 5, 0, 15),
        AllocationTarget("reits", 5, 0, 10),
    ],
)
