"""
§1, §15, §26, §27 — Asset and portfolio data models.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AssetRole(Enum):
    CORE = "core"
    SATELLITE = "satellite"


class VehicleType(Enum):
    ETF = "etf"
    FUND = "fund"  # mutual fund eligible for Spanish tax-free transfer
    INDEX = "index"
    OTHER = "other"


class HistoryType(Enum):
    LIVE_FUND = "live_fund"
    LIVE_INDEX = "live_index"
    BACKTESTED_INDEX = "backtested_index"
    SIMULATED = "simulated"


class AccumulationType(Enum):
    ACCUMULATING = "accumulating"
    DISTRIBUTING = "distributing"


@dataclass
class Asset:
    ticker: str
    name: str
    isin: Optional[str] = None
    vehicle_type: VehicleType = VehicleType.ETF
    role: AssetRole = AssetRole.SATELLITE
    accumulation: AccumulationType = AccumulationType.ACCUMULATING
    ter_pct: float = 0.0
    aum_millions: float = 0.0
    inception_date: Optional[str] = None
    underlying_index: Optional[str] = None
    underlying_index_inception: Optional[str] = None
    history_type: HistoryType = HistoryType.LIVE_FUND
    currency: str = "EUR"
    is_transferable_spain: bool = False  # §34 traspasabilidad
    tags: list[str] = field(default_factory=list)


@dataclass
class PortfolioPosition:
    asset: Asset
    weight_pct: float
    strategic_weight_pct: float  # §35 strategic allocation target
    role: AssetRole = AssetRole.CORE


@dataclass
class Portfolio:
    name: str
    positions: list[PortfolioPosition] = field(default_factory=list)
    initial_capital: float = 100_000.0
    monthly_contribution: float = 0.0
    annual_contribution_growth_pct: float = 0.0
    horizon_years: int = 40

    @property
    def core_positions(self) -> list[PortfolioPosition]:
        return [p for p in self.positions if p.role == AssetRole.CORE]

    @property
    def satellite_positions(self) -> list[PortfolioPosition]:
        return [p for p in self.positions if p.role == AssetRole.SATELLITE]

    @property
    def total_ter(self) -> float:
        return sum(p.weight_pct / 100 * p.asset.ter_pct for p in self.positions)

    @property
    def position_count(self) -> int:
        return len(self.positions)
