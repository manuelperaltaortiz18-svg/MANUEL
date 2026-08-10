"""
Sector Investment Analysis Engine — full value-chain decomposition,
structural scoring, and long-term opportunity identification.

Covers all 11 GICS sectors, their industries and sub-industries,
representative ETFs, and key publicly traded companies across the
value chain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── GICS TAXONOMY ────────────────────────────────────────────────────

class GICSSector(Enum):
    TECHNOLOGY = "Information Technology"
    HEALTHCARE = "Health Care"
    FINANCIALS = "Financials"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    INDUSTRIALS = "Industrials"
    ENERGY = "Energy"
    MATERIALS = "Materials"
    UTILITIES = "Utilities"
    REAL_ESTATE = "Real Estate"
    COMMUNICATION_SERVICES = "Communication Services"


class CyclePhase(Enum):
    EARLY_EXPANSION = "early_expansion"
    MID_EXPANSION = "mid_expansion"
    LATE_EXPANSION = "late_expansion"
    RECESSION = "recession"
    RECOVERY = "recovery"


class ValueChainPosition(Enum):
    UPSTREAM = "upstream"
    MIDSTREAM = "midstream"
    DOWNSTREAM = "downstream"
    ENABLING = "enabling"
    INTEGRATED = "integrated"


class CompetitiveDynamics(Enum):
    MONOPOLY = "monopoly"
    OLIGOPOLY = "oligopoly"
    FRAGMENTED = "fragmented"
    CONSOLIDATING = "consolidating"
    DISRUPTING = "disrupting"


class MoatType(Enum):
    NETWORK_EFFECTS = "network_effects"
    SWITCHING_COSTS = "switching_costs"
    INTANGIBLE_ASSETS = "intangible_assets"
    COST_ADVANTAGE = "cost_advantage"
    EFFICIENT_SCALE = "efficient_scale"
    NONE = "none"


# ─── VALUE CHAIN SEGMENT ─────────────────────────────────────────────

@dataclass
class ValueChainSegment:
    """A segment within a sector's value chain."""
    name: str
    position: ValueChainPosition
    description: str
    key_companies: list[str] = field(default_factory=list)
    key_etfs: list[str] = field(default_factory=list)
    competitive_dynamics: CompetitiveDynamics = CompetitiveDynamics.FRAGMENTED
    primary_moats: list[MoatType] = field(default_factory=list)
    margin_profile: str = ""  # e.g. "gross 60-70%, operating 20-30%"
    secular_trends: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    capex_intensity: str = "medium"  # low / medium / high
    regulatory_exposure: str = "medium"


# ─── SECTOR SCORING ──────────────────────────────────────────────────

@dataclass
class SectorStructuralScore:
    """Long-term structural attractiveness of a sector (0–100)."""
    secular_growth: float = 0       # TAM expansion, demographic/tech tailwinds
    pricing_power: float = 0        # ability to pass through inflation
    margin_trajectory: float = 0    # expanding, stable, compressing
    innovation_intensity: float = 0 # R&D spend, patent activity, disruption pace
    barriers_to_entry: float = 0    # moats, capital requirements, regulation
    capital_efficiency: float = 0   # ROIC, asset-light vs heavy
    cash_generation: float = 0     # FCF conversion, working capital needs
    esg_alignment: float = 0       # regulatory tailwinds, social license

    @property
    def total(self) -> float:
        weights = {
            "secular_growth": 0.20,
            "pricing_power": 0.15,
            "margin_trajectory": 0.12,
            "innovation_intensity": 0.10,
            "barriers_to_entry": 0.13,
            "capital_efficiency": 0.12,
            "cash_generation": 0.10,
            "esg_alignment": 0.08,
        }
        return round(sum(getattr(self, k) * v for k, v in weights.items()), 1)


@dataclass
class SectorCyclicalScore:
    """Where is this sector in its cycle? (0–100, higher = more favorable)."""
    earnings_momentum: float = 0    # y/y earnings revisions
    relative_valuation: float = 0   # vs own history and vs market
    credit_conditions: float = 0    # access to capital, spread levels
    inventory_cycle: float = 0      # destocking/restocking position
    capex_cycle: float = 0          # under/over-investment phase
    labor_market: float = 0         # wage pressure, talent availability
    policy_environment: float = 0   # fiscal/monetary/regulatory stance

    @property
    def total(self) -> float:
        weights = {
            "earnings_momentum": 0.20,
            "relative_valuation": 0.20,
            "credit_conditions": 0.15,
            "inventory_cycle": 0.10,
            "capex_cycle": 0.10,
            "labor_market": 0.10,
            "policy_environment": 0.15,
        }
        return round(sum(getattr(self, k) * v for k, v in weights.items()), 1)


@dataclass
class SectorRiskScore:
    """Sector-level risk assessment (0–100, lower is better)."""
    regulatory_risk: float = 0
    technological_disruption: float = 0
    geopolitical_exposure: float = 0
    concentration_risk: float = 0   # top-heavy sector
    leverage_risk: float = 0
    commodity_sensitivity: float = 0
    currency_risk: float = 0
    tail_risk: float = 0            # black swan vulnerability

    @property
    def total(self) -> float:
        weights = {
            "regulatory_risk": 0.15,
            "technological_disruption": 0.15,
            "geopolitical_exposure": 0.12,
            "concentration_risk": 0.13,
            "leverage_risk": 0.12,
            "commodity_sensitivity": 0.10,
            "currency_risk": 0.10,
            "tail_risk": 0.13,
        }
        return round(sum(getattr(self, k) * v for k, v in weights.items()), 1)


@dataclass
class SectorCompoundingProfile:
    """How well does this sector compound wealth over 20-40 years?"""
    historical_real_cagr_20y: Optional[float] = None  # annualized
    historical_real_cagr_40y: Optional[float] = None
    dividend_contribution_pct: float = 0  # % of total return from dividends
    buyback_yield_avg: float = 0
    earnings_growth_cagr: float = 0
    multiple_expansion_contribution: float = 0  # + or -
    reinvestment_rate: float = 0  # % of earnings reinvested
    payout_consistency: float = 0  # 0-100

    @property
    def total_shareholder_yield(self) -> float:
        return self.dividend_contribution_pct + self.buyback_yield_avg

    @property
    def organic_growth_quality(self) -> float:
        if self.earnings_growth_cagr <= 0:
            return 0
        reinvestment_quality = min(
            self.reinvestment_rate * self.earnings_growth_cagr * 100, 100
        )
        return round(reinvestment_quality, 1)


# ─── SECTOR PROFILE ──────────────────────────────────────────────────

@dataclass
class SectorProfile:
    """Complete analytical profile of a GICS sector."""
    sector: GICSSector
    value_chain: list[ValueChainSegment] = field(default_factory=list)
    structural_score: SectorStructuralScore = field(
        default_factory=SectorStructuralScore
    )
    cyclical_score: SectorCyclicalScore = field(
        default_factory=SectorCyclicalScore
    )
    risk_score: SectorRiskScore = field(default_factory=SectorRiskScore)
    compounding_profile: SectorCompoundingProfile = field(
        default_factory=SectorCompoundingProfile
    )
    primary_etfs: list[str] = field(default_factory=list)
    preferred_cycle_phases: list[CyclePhase] = field(default_factory=list)
    correlation_to_sp500: float = 0
    beta: float = 1.0
    weight_in_sp500_pct: float = 0
    notes: str = ""

    @property
    def composite_score(self) -> float:
        structural = self.structural_score.total
        cyclical = self.cyclical_score.total
        risk_inv = 100 - self.risk_score.total
        return round(
            structural * 0.50 + cyclical * 0.25 + risk_inv * 0.25, 1
        )

    @property
    def investment_verdict(self) -> str:
        score = self.composite_score
        if score >= 75:
            return "STRONG OVERWEIGHT"
        if score >= 65:
            return "OVERWEIGHT"
        if score >= 50:
            return "MARKET WEIGHT"
        if score >= 40:
            return "UNDERWEIGHT"
        return "STRONG UNDERWEIGHT"


# ─── OPPORTUNITY IDENTIFICATION ───────────────────────────────────────

@dataclass
class SectorOpportunity:
    """An identified investment opportunity within a sector."""
    sector: GICSSector
    segment: str
    thesis: str
    vehicle_type: str  # "ETF", "single_stock", "fund"
    tickers: list[str] = field(default_factory=list)
    time_horizon: str = "long_term"  # short_term, medium_term, long_term
    conviction: str = "medium"  # low, medium, high
    catalysts: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    expected_cagr_range: tuple[float, float] = (0.0, 0.0)
    fit_for_core: bool = False
    fit_for_satellite: bool = True


# ─── SECTOR DATABASE ─────────────────────────────────────────────────

def build_sector_database() -> dict[GICSSector, SectorProfile]:
    """
    Reference database of all 11 GICS sectors with full value-chain
    decomposition, representative ETFs, and key companies.
    """
    db: dict[GICSSector, SectorProfile] = {}

    # ── INFORMATION TECHNOLOGY ────────────────────────────────────
    db[GICSSector.TECHNOLOGY] = SectorProfile(
        sector=GICSSector.TECHNOLOGY,
        value_chain=[
            ValueChainSegment(
                name="Semiconductors & Equipment",
                position=ValueChainPosition.UPSTREAM,
                description="Chip design, fabrication, equipment, and EDA tools",
                key_companies=[
                    "NVDA", "TSM", "ASML", "AMD", "AVGO", "INTC",
                    "QCOM", "TXN", "LRCX", "AMAT", "KLAC", "MRVL",
                    "ON", "SNPS", "CDNS", "ARM",
                ],
                key_etfs=["SMH", "SOXX", "XSD"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.COST_ADVANTAGE, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 50-65%, operating 25-45%",
                secular_trends=[
                    "AI/ML compute demand", "edge computing",
                    "automotive electrification", "IoT proliferation",
                    "data center expansion", "sovereign chip programs",
                ],
                risks=[
                    "cyclicality", "geopolitical (China/Taiwan)",
                    "capex intensity", "customer concentration",
                ],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Software & Cloud Infrastructure",
                position=ValueChainPosition.MIDSTREAM,
                description="Enterprise software, cloud platforms, SaaS, cybersecurity",
                key_companies=[
                    "MSFT", "ORCL", "CRM", "NOW", "ADBE", "INTU",
                    "PANW", "CRWD", "FTNT", "SNOW", "DDOG", "MDB",
                    "WDAY", "TEAM", "ZS", "HUBS",
                ],
                key_etfs=["IGV", "SKYY", "WCLD", "BUG", "HACK"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.NETWORK_EFFECTS],
                margin_profile="gross 70-85%, operating 20-40%",
                secular_trends=[
                    "cloud migration", "AI integration",
                    "cybersecurity spend", "digital transformation",
                    "vertical SaaS", "API economy",
                ],
                risks=[
                    "valuation compression", "open source competition",
                    "AI commoditization of features", "macro sensitivity on deals",
                ],
                capex_intensity="low",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="IT Hardware & Devices",
                position=ValueChainPosition.DOWNSTREAM,
                description="PCs, phones, networking equipment, storage",
                key_companies=[
                    "AAPL", "DELL", "HPQ", "HPE", "CSCO",
                    "ANET", "KEYS", "CDW", "ZBRA",
                ],
                key_etfs=["XLK", "FTEC"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 35-45%, operating 15-25%",
                secular_trends=[
                    "AI-ready infrastructure", "networking upgrades",
                    "edge devices", "AR/VR hardware",
                ],
                risks=[
                    "commoditization", "supply chain disruption",
                    "replacement cycle lengthening",
                ],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="IT Services & Consulting",
                position=ValueChainPosition.ENABLING,
                description="Systems integration, outsourcing, consulting",
                key_companies=[
                    "ACN", "IBM", "CTSH", "INFY", "WIT", "EPAM", "GLOB",
                ],
                key_etfs=["IGV"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.SWITCHING_COSTS],
                margin_profile="gross 30-40%, operating 12-18%",
                secular_trends=[
                    "AI transformation services",
                    "cloud migration consulting",
                    "managed security services",
                ],
                risks=["AI displacement of services", "talent availability", "offshoring pressure"],
                capex_intensity="low",
                regulatory_exposure="low",
            ),
            ValueChainSegment(
                name="Payments & Fintech Infrastructure",
                position=ValueChainPosition.ENABLING,
                description="Payment networks, processing, financial technology platforms",
                key_companies=[
                    "V", "MA", "PYPL", "SQ", "FIS", "FISV",
                    "GPN", "ADYEN", "TOST",
                ],
                key_etfs=["IPAY", "FINX"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.NETWORK_EFFECTS, MoatType.EFFICIENT_SCALE],
                margin_profile="gross 55-80%, operating 35-55%",
                secular_trends=[
                    "cashless economy", "cross-border digital payments",
                    "embedded finance", "B2B payments digitization",
                ],
                risks=["regulation", "CBDC competition", "interchange fee pressure"],
                capex_intensity="low",
                regulatory_exposure="high",
            ),
        ],
        primary_etfs=["XLK", "VGT", "QQQ", "FTEC", "IYW"],
        preferred_cycle_phases=[
            CyclePhase.EARLY_EXPANSION, CyclePhase.MID_EXPANSION,
        ],
        beta=1.15,
        weight_in_sp500_pct=31.5,
    )

    # ── HEALTH CARE ───────────────────────────────────────────────
    db[GICSSector.HEALTHCARE] = SectorProfile(
        sector=GICSSector.HEALTHCARE,
        value_chain=[
            ValueChainSegment(
                name="Pharmaceuticals",
                position=ValueChainPosition.DOWNSTREAM,
                description="Large-cap drug developers with diversified pipelines",
                key_companies=[
                    "LLY", "JNJ", "MRK", "ABBV", "PFE", "NVS",
                    "AZN", "BMY", "AMGN", "SNY", "GSK", "NVO",
                ],
                key_etfs=["XLV", "IHE", "PPH"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 65-80%, operating 25-40%",
                secular_trends=[
                    "GLP-1 / obesity therapeutics", "Alzheimer's treatments",
                    "gene therapy", "aging populations",
                    "oncology precision medicine",
                ],
                risks=["patent cliffs", "pricing regulation", "pipeline failures"],
                capex_intensity="medium",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Biotechnology",
                position=ValueChainPosition.UPSTREAM,
                description="Drug discovery, biologics, genomics, CRISPR",
                key_companies=[
                    "VRTX", "GILD", "REGN", "MRNA", "BIIB",
                    "ALNY", "BMRN", "SGEN", "CRSP", "NTLA", "BEAM",
                ],
                key_etfs=["IBB", "XBI", "ARKG"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.INTANGIBLE_ASSETS],
                margin_profile="varies: -50% to +60% operating",
                secular_trends=[
                    "gene editing / CRISPR", "mRNA platforms",
                    "cell therapy", "antibody-drug conjugates",
                    "AI drug discovery",
                ],
                risks=["binary clinical trial outcomes", "funding sensitivity", "regulatory hurdles"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Medical Devices & Equipment",
                position=ValueChainPosition.MIDSTREAM,
                description="Surgical robots, implants, diagnostics, imaging",
                key_companies=[
                    "ABT", "MDT", "SYK", "ISRG", "BSX", "EW",
                    "BDX", "DXCM", "HOLX", "IDXX", "ZBH",
                ],
                key_etfs=["IHI"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 55-70%, operating 20-30%",
                secular_trends=[
                    "robotic surgery", "continuous glucose monitoring",
                    "minimally invasive procedures", "AI diagnostics",
                    "wearable health tech",
                ],
                risks=["reimbursement pressure", "product recalls", "competition from big tech"],
                capex_intensity="medium",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Healthcare Services & Managed Care",
                position=ValueChainPosition.DOWNSTREAM,
                description="Insurers, hospital operators, PBMs, distributors",
                key_companies=[
                    "UNH", "ELV", "CI", "HUM", "CNC", "MOH",
                    "HCA", "THC", "MCK", "ABC", "CAH",
                ],
                key_etfs=["XLV", "IHF"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.SWITCHING_COSTS],
                margin_profile="gross 20-30%, operating 5-10%",
                secular_trends=[
                    "value-based care", "Medicare Advantage growth",
                    "vertical integration", "home health expansion",
                ],
                risks=["political/regulatory risk", "medical cost inflation", "antitrust"],
                capex_intensity="low",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Life Sciences Tools & CROs",
                position=ValueChainPosition.ENABLING,
                description="Instruments, reagents, contract research, CDMO",
                key_companies=[
                    "TMO", "DHR", "A", "IQV", "WST",
                    "TECH", "BIO", "CRL", "MTD",
                ],
                key_etfs=["XLV"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.COST_ADVANTAGE],
                margin_profile="gross 50-60%, operating 20-30%",
                secular_trends=[
                    "biotech outsourcing", "biologics manufacturing",
                    "precision medicine analytics", "lab automation",
                ],
                risks=["biotech funding cycles", "China revenue exposure", "M&A integration"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
        ],
        primary_etfs=["XLV", "VHT", "IYH", "FHLC"],
        preferred_cycle_phases=[
            CyclePhase.LATE_EXPANSION, CyclePhase.RECESSION,
        ],
        beta=0.80,
        weight_in_sp500_pct=12.0,
    )

    # ── FINANCIALS ────────────────────────────────────────────────
    db[GICSSector.FINANCIALS] = SectorProfile(
        sector=GICSSector.FINANCIALS,
        value_chain=[
            ValueChainSegment(
                name="Diversified Banks",
                position=ValueChainPosition.INTEGRATED,
                description="Universal banks: lending, deposits, capital markets, wealth mgmt",
                key_companies=[
                    "JPM", "BAC", "WFC", "C", "GS", "MS",
                    "USB", "PNC", "TFC", "SCHW",
                ],
                key_etfs=["XLF", "KBE", "KRE"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.SWITCHING_COSTS],
                margin_profile="NIM 2.5-3.5%, ROE 12-18%",
                secular_trends=[
                    "digital banking", "wealth management TAM growth",
                    "capital markets activity", "payments modernization",
                ],
                risks=["credit cycle", "interest rate sensitivity", "regulation", "fintech disruption"],
                capex_intensity="low",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Insurance",
                position=ValueChainPosition.DOWNSTREAM,
                description="P&C, life, reinsurance, specialty",
                key_companies=[
                    "BRK.B", "PGR", "ALL", "TRV", "MET",
                    "AFL", "AIG", "CB", "HIG", "RNR",
                ],
                key_etfs=["KIE", "IAK"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.COST_ADVANTAGE, MoatType.EFFICIENT_SCALE],
                margin_profile="combined ratio 90-100%, ROE 10-15%",
                secular_trends=[
                    "hard pricing cycle", "climate risk repricing",
                    "insurtech", "specialty lines growth",
                ],
                risks=["catastrophe losses", "reserve adequacy", "investment portfolio risk"],
                capex_intensity="low",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Asset Management & Exchanges",
                position=ValueChainPosition.ENABLING,
                description="Asset managers, exchanges, data providers, index providers",
                key_companies=[
                    "BLK", "BX", "KKR", "APO", "ARES", "CG",
                    "ICE", "CME", "NDAQ", "MSCI", "SPGI", "MCO",
                ],
                key_etfs=["XLF"],
                competitive_dynamics=CompetitiveDynamics.CONSOLIDATING,
                primary_moats=[MoatType.NETWORK_EFFECTS, MoatType.SWITCHING_COSTS],
                margin_profile="operating 30-55%",
                secular_trends=[
                    "passive investing growth", "alternative assets AUM",
                    "private credit expansion", "data monetization",
                ],
                risks=["fee compression", "AUM sensitivity to markets", "regulatory changes"],
                capex_intensity="low",
                regulatory_exposure="medium",
            ),
        ],
        primary_etfs=["XLF", "VFH", "IYF", "FNCL"],
        preferred_cycle_phases=[
            CyclePhase.EARLY_EXPANSION, CyclePhase.MID_EXPANSION,
        ],
        beta=1.10,
        weight_in_sp500_pct=13.0,
    )

    # ── CONSUMER DISCRETIONARY ────────────────────────────────────
    db[GICSSector.CONSUMER_DISCRETIONARY] = SectorProfile(
        sector=GICSSector.CONSUMER_DISCRETIONARY,
        value_chain=[
            ValueChainSegment(
                name="E-Commerce & Internet Retail",
                position=ValueChainPosition.DOWNSTREAM,
                description="Online marketplaces, D2C, fulfillment platforms",
                key_companies=[
                    "AMZN", "BABA", "MELI", "SE", "PDD",
                    "EBAY", "ETSY", "W", "CPNG",
                ],
                key_etfs=["IBUY", "ONLN"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.NETWORK_EFFECTS, MoatType.COST_ADVANTAGE],
                margin_profile="gross 40-60%, operating 2-15%",
                secular_trends=[
                    "e-commerce penetration growth globally",
                    "same-day delivery", "social commerce",
                    "cross-border e-commerce",
                ],
                risks=["competition", "margin pressure", "logistics costs", "regulation"],
                capex_intensity="high",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Luxury & Premium Brands",
                position=ValueChainPosition.DOWNSTREAM,
                description="Luxury goods, premium apparel, aspirational brands",
                key_companies=[
                    "LVMUY", "RMS.PA", "MC.PA", "KER.PA",
                    "NKE", "LULU", "TPR", "RL", "CPRI",
                ],
                key_etfs=["LUXE"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 65-75%, operating 25-40%",
                secular_trends=[
                    "emerging market wealth creation",
                    "experiential luxury", "digital engagement",
                    "Gen Z luxury adoption",
                ],
                risks=["China demand sensitivity", "brand dilution", "counterfeit risk"],
                capex_intensity="medium",
                regulatory_exposure="low",
            ),
            ValueChainSegment(
                name="Automotive & EV",
                position=ValueChainPosition.INTEGRATED,
                description="Traditional OEMs, EV manufacturers, auto parts",
                key_companies=[
                    "TSLA", "TM", "F", "GM", "RIVN",
                    "STLA", "BWA", "APH", "ALV", "LEA",
                ],
                key_etfs=["CARZ", "DRIV", "IDRV"],
                competitive_dynamics=CompetitiveDynamics.DISRUPTING,
                primary_moats=[MoatType.COST_ADVANTAGE, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 15-25%, operating 5-12%",
                secular_trends=[
                    "EV adoption curve", "autonomous driving",
                    "connected vehicles", "fleet electrification",
                ],
                risks=["capital intensity", "EV pricing wars", "battery supply chain", "regulation"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Restaurants, Travel & Leisure",
                position=ValueChainPosition.DOWNSTREAM,
                description="QSR, casual dining, hotels, OTAs, cruise lines, gaming",
                key_companies=[
                    "MCD", "SBUX", "CMG", "YUM", "DPZ",
                    "MAR", "HLT", "BKNG", "ABNB", "EXPE",
                    "RCL", "LVS", "WYNN", "MGM",
                ],
                key_etfs=["PEJ", "JETS", "BJK"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.INTANGIBLE_ASSETS, MoatType.NETWORK_EFFECTS],
                margin_profile="gross 30-65%, operating 15-30%",
                secular_trends=[
                    "experience economy", "loyalty program monetization",
                    "franchise-light models", "travel recovery",
                ],
                risks=["consumer spending sensitivity", "labor costs", "geopolitical events"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Home & Home Improvement",
                position=ValueChainPosition.DOWNSTREAM,
                description="Home improvement retail, homebuilders, furnishings",
                key_companies=[
                    "HD", "LOW", "DHI", "LEN", "PHM",
                    "NVR", "WSM", "RH", "BLDR",
                ],
                key_etfs=["XHB", "ITB"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.COST_ADVANTAGE],
                margin_profile="gross 30-45%, operating 10-18%",
                secular_trends=[
                    "housing underbuilding", "aging housing stock",
                    "remote work renovations", "millennial homeownership",
                ],
                risks=["interest rate sensitivity", "housing cycle", "input cost inflation"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
        ],
        primary_etfs=["XLY", "VCR", "IYC", "FDIS"],
        preferred_cycle_phases=[
            CyclePhase.EARLY_EXPANSION, CyclePhase.RECOVERY,
        ],
        beta=1.15,
        weight_in_sp500_pct=10.5,
    )

    # ── CONSUMER STAPLES ──────────────────────────────────────────
    db[GICSSector.CONSUMER_STAPLES] = SectorProfile(
        sector=GICSSector.CONSUMER_STAPLES,
        value_chain=[
            ValueChainSegment(
                name="Food & Beverage",
                position=ValueChainPosition.INTEGRATED,
                description="Packaged food, beverages, snacks, dairy",
                key_companies=[
                    "KO", "PEP", "NESN", "MDLZ", "GIS",
                    "K", "HSY", "SJM", "CAG", "CPB", "BN",
                ],
                key_etfs=["XLP", "VDC", "PBJ"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.INTANGIBLE_ASSETS, MoatType.COST_ADVANTAGE],
                margin_profile="gross 35-55%, operating 15-25%",
                secular_trends=[
                    "health & wellness", "premiumization",
                    "emerging market penetration", "plant-based alternatives",
                ],
                risks=["input cost inflation", "private label competition", "volume declines"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Household & Personal Care",
                position=ValueChainPosition.DOWNSTREAM,
                description="Cleaning, personal care, cosmetics",
                key_companies=[
                    "PG", "UL", "CL", "EL", "CHD", "CLX", "HPC",
                ],
                key_etfs=["XLP"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.INTANGIBLE_ASSETS, MoatType.COST_ADVANTAGE],
                margin_profile="gross 50-60%, operating 20-25%",
                secular_trends=[
                    "premiumization", "sustainability",
                    "D2C channel", "emerging market middle class",
                ],
                risks=["raw material costs", "e-commerce disruption", "brand fatigue"],
                capex_intensity="medium",
                regulatory_exposure="low",
            ),
            ValueChainSegment(
                name="Food & Drug Retail",
                position=ValueChainPosition.DOWNSTREAM,
                description="Supermarkets, pharmacies, warehouse clubs",
                key_companies=[
                    "WMT", "COST", "KR", "TGT", "DG",
                    "DLTR", "SYY", "ADM",
                ],
                key_etfs=["XLP", "XRT"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.COST_ADVANTAGE, MoatType.EFFICIENT_SCALE],
                margin_profile="gross 25-35%, operating 3-8%",
                secular_trends=[
                    "grocery e-commerce", "private label growth",
                    "automation", "health-focused assortment",
                ],
                risks=["margin pressure", "e-commerce competition", "labor costs"],
                capex_intensity="medium",
                regulatory_exposure="low",
            ),
            ValueChainSegment(
                name="Tobacco & Alcohol",
                position=ValueChainPosition.DOWNSTREAM,
                description="Cigarettes, reduced-risk products, spirits, beer, wine",
                key_companies=[
                    "PM", "MO", "BTI", "DEO", "BF.B",
                    "STZ", "SAM", "TAP",
                ],
                key_etfs=["XLP"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.INTANGIBLE_ASSETS, MoatType.EFFICIENT_SCALE],
                margin_profile="gross 55-70%, operating 35-50%",
                secular_trends=[
                    "reduced-risk products (vaping, heated tobacco)",
                    "premiumization in spirits", "seltzer/RTD cocktails",
                ],
                risks=["regulation", "ESG exclusion", "volume decline", "litigation"],
                capex_intensity="low",
                regulatory_exposure="high",
            ),
        ],
        primary_etfs=["XLP", "VDC", "IYK", "FSTA"],
        preferred_cycle_phases=[
            CyclePhase.LATE_EXPANSION, CyclePhase.RECESSION,
        ],
        beta=0.65,
        weight_in_sp500_pct=6.0,
    )

    # ── INDUSTRIALS ───────────────────────────────────────────────
    db[GICSSector.INDUSTRIALS] = SectorProfile(
        sector=GICSSector.INDUSTRIALS,
        value_chain=[
            ValueChainSegment(
                name="Aerospace & Defense",
                position=ValueChainPosition.INTEGRATED,
                description="Commercial aerospace, defense systems, space",
                key_companies=[
                    "BA", "LMT", "RTX", "GD", "NOC",
                    "LHX", "HII", "TDG", "HEI", "AXON",
                ],
                key_etfs=["ITA", "XAR", "PPA"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 25-40%, operating 10-25%",
                secular_trends=[
                    "defense spending cycle upturn globally",
                    "commercial fleet renewal", "space economy",
                    "autonomous systems", "cybersecurity in defense",
                ],
                risks=["program execution", "government spending cuts", "supply chain"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Capital Goods & Machinery",
                position=ValueChainPosition.MIDSTREAM,
                description="Industrial equipment, automation, robotics",
                key_companies=[
                    "CAT", "DE", "HON", "GE", "EMR",
                    "ROK", "ETN", "PH", "IR", "AME",
                    "CMI", "OTIS", "DOV",
                ],
                key_etfs=["XLI", "VIS"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.COST_ADVANTAGE],
                margin_profile="gross 35-45%, operating 15-25%",
                secular_trends=[
                    "factory automation / Industry 4.0",
                    "reshoring / nearshoring", "electrification",
                    "infrastructure investment cycle",
                ],
                risks=["cyclicality", "trade policy", "input costs"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Transportation & Logistics",
                position=ValueChainPosition.ENABLING,
                description="Railroads, airlines, trucking, logistics, delivery",
                key_companies=[
                    "UNP", "CSX", "NSC", "UPS", "FDX",
                    "DAL", "LUV", "UAL", "JBHT", "XPO", "ODFL",
                ],
                key_etfs=["IYT", "XTN"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.COST_ADVANTAGE],
                margin_profile="operating 10-30% (rails highest)",
                secular_trends=[
                    "e-commerce logistics", "intermodal shift",
                    "fuel efficiency / sustainability",
                    "autonomous trucking / drones",
                ],
                risks=["fuel costs", "labor relations", "economic sensitivity", "overcapacity"],
                capex_intensity="high",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Professional & Commercial Services",
                position=ValueChainPosition.ENABLING,
                description="Staffing, waste management, security, consulting",
                key_companies=[
                    "WM", "RSG", "VRSK", "CTAS", "PAYX",
                    "ADP", "BR", "LDOS", "BAH",
                ],
                key_etfs=["XLI"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.EFFICIENT_SCALE],
                margin_profile="gross 35-50%, operating 15-25%",
                secular_trends=[
                    "outsourcing trend", "environmental services",
                    "data analytics in services",
                ],
                risks=["labor shortages", "pricing pressure", "commoditization"],
                capex_intensity="low",
                regulatory_exposure="medium",
            ),
        ],
        primary_etfs=["XLI", "VIS", "IYJ", "FIDU"],
        preferred_cycle_phases=[
            CyclePhase.EARLY_EXPANSION, CyclePhase.MID_EXPANSION,
        ],
        beta=1.05,
        weight_in_sp500_pct=8.5,
    )

    # ── ENERGY ────────────────────────────────────────────────────
    db[GICSSector.ENERGY] = SectorProfile(
        sector=GICSSector.ENERGY,
        value_chain=[
            ValueChainSegment(
                name="Exploration & Production (E&P)",
                position=ValueChainPosition.UPSTREAM,
                description="Oil & gas exploration, drilling, production",
                key_companies=[
                    "XOM", "CVX", "COP", "EOG", "PXD",
                    "DVN", "FANG", "MRO", "OXY", "HES",
                ],
                key_etfs=["XOP", "IEO"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.COST_ADVANTAGE],
                margin_profile="operating 20-40% (highly variable)",
                secular_trends=[
                    "capital discipline", "shareholder returns focus",
                    "LNG growth", "Permian dominance",
                ],
                risks=["commodity price volatility", "ESG divestment", "transition risk", "geopolitics"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Midstream (Pipelines & Infrastructure)",
                position=ValueChainPosition.MIDSTREAM,
                description="Pipelines, storage, processing, LNG terminals",
                key_companies=[
                    "ENB", "WMB", "KMI", "ET", "EPD",
                    "MPLX", "OKE", "TRGP",
                ],
                key_etfs=["AMLP", "MLPA", "EMLP"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.COST_ADVANTAGE],
                margin_profile="EBITDA margins 50-70%, fee-based",
                secular_trends=[
                    "LNG export capacity buildout",
                    "natural gas demand for power generation",
                    "hydrogen infrastructure optionality",
                ],
                risks=["regulatory / permitting", "volume sensitivity", "leverage"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Refining & Marketing",
                position=ValueChainPosition.DOWNSTREAM,
                description="Petroleum refining, fuel distribution, retail",
                key_companies=[
                    "MPC", "VLO", "PSX", "DINO", "PBF",
                ],
                key_etfs=["XLE", "CRAK"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.COST_ADVANTAGE, MoatType.EFFICIENT_SCALE],
                margin_profile="crack spread dependent, operating 5-15%",
                secular_trends=[
                    "capacity rationalization",
                    "biofuels / renewable diesel",
                    "petrochemical integration",
                ],
                risks=["crack spread volatility", "EV transition demand destruction", "regulation"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Oilfield Services & Equipment",
                position=ValueChainPosition.ENABLING,
                description="Drilling services, completion, equipment manufacturers",
                key_companies=[
                    "SLB", "HAL", "BKR", "FTI", "NOV",
                    "CHX", "WHD",
                ],
                key_etfs=["OIH", "IEZ"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 20-30%, operating 10-20%",
                secular_trends=[
                    "international recovery", "digital oilfield",
                    "deepwater resurgence", "efficiency gains",
                ],
                risks=["E&P capex cycles", "pricing pressure", "energy transition"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Clean Energy & Renewables",
                position=ValueChainPosition.INTEGRATED,
                description="Solar, wind, hydrogen, energy storage, clean utilities",
                key_companies=[
                    "ENPH", "SEDG", "FSLR", "NEE", "RUN",
                    "PLUG", "BE", "NOVA", "CSIQ", "AES",
                ],
                key_etfs=["ICLN", "TAN", "QCLN", "FAN", "PBW"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.COST_ADVANTAGE],
                margin_profile="gross 20-40%, operating 5-20%",
                secular_trends=[
                    "IRA / policy support", "grid-scale storage",
                    "corporate PPAs", "green hydrogen",
                    "declining levelized cost of energy",
                ],
                risks=[
                    "policy dependency", "interest rate sensitivity",
                    "overcapacity", "technology obsolescence",
                    "permitting delays",
                ],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
        ],
        primary_etfs=["XLE", "VDE", "IYE", "FENY"],
        preferred_cycle_phases=[
            CyclePhase.MID_EXPANSION, CyclePhase.LATE_EXPANSION,
        ],
        beta=1.20,
        weight_in_sp500_pct=3.5,
    )

    # ── MATERIALS ─────────────────────────────────────────────────
    db[GICSSector.MATERIALS] = SectorProfile(
        sector=GICSSector.MATERIALS,
        value_chain=[
            ValueChainSegment(
                name="Metals & Mining",
                position=ValueChainPosition.UPSTREAM,
                description="Gold, copper, lithium, iron ore, diversified miners",
                key_companies=[
                    "BHP", "RIO", "VALE", "FCX", "NEM",
                    "GOLD", "SCCO", "TECK", "NUE", "STLD", "ALB",
                ],
                key_etfs=["XME", "GDX", "SIL", "PICK", "LIT", "COPX"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.COST_ADVANTAGE],
                margin_profile="EBITDA 30-50%, highly cyclical",
                secular_trends=[
                    "electrification metals demand (Cu, Li, Ni)",
                    "gold as monetary hedge", "reshoring demand for steel",
                    "critical minerals security",
                ],
                risks=["commodity price volatility", "ESG/permitting", "geopolitics", "water access"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Chemicals",
                position=ValueChainPosition.MIDSTREAM,
                description="Specialty chemicals, commodity chemicals, ag chemicals",
                key_companies=[
                    "LIN", "APD", "SHW", "ECL", "DD",
                    "PPG", "DOW", "LYB", "CE", "FMC", "CF",
                ],
                key_etfs=["XLB", "VAW"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.COST_ADVANTAGE, MoatType.SWITCHING_COSTS],
                margin_profile="gross 30-55%, operating 15-25%",
                secular_trends=[
                    "specialty chemical premiumization",
                    "industrial gases growth", "sustainability solutions",
                    "semiconductor chemical demand",
                ],
                risks=["feedstock costs", "overcapacity", "regulation", "China competition"],
                capex_intensity="high",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Construction Materials & Packaging",
                position=ValueChainPosition.DOWNSTREAM,
                description="Aggregates, cement, packaging materials",
                key_companies=[
                    "VMC", "MLM", "CX", "BALL", "PKG",
                    "IP", "BLL", "SEE", "AMCR",
                ],
                key_etfs=["XLB"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.COST_ADVANTAGE],
                margin_profile="gross 25-40%, operating 12-22%",
                secular_trends=[
                    "infrastructure spending", "sustainable packaging",
                    "nearshoring construction",
                ],
                risks=["housing cycle", "energy costs", "environmental regulation"],
                capex_intensity="high",
                regulatory_exposure="medium",
            ),
        ],
        primary_etfs=["XLB", "VAW", "IYM", "FMAT"],
        preferred_cycle_phases=[
            CyclePhase.EARLY_EXPANSION, CyclePhase.MID_EXPANSION,
        ],
        beta=1.10,
        weight_in_sp500_pct=2.5,
    )

    # ── UTILITIES ─────────────────────────────────────────────────
    db[GICSSector.UTILITIES] = SectorProfile(
        sector=GICSSector.UTILITIES,
        value_chain=[
            ValueChainSegment(
                name="Regulated Electric Utilities",
                position=ValueChainPosition.INTEGRATED,
                description="Rate-regulated power generation, transmission, distribution",
                key_companies=[
                    "NEE", "SO", "DUK", "D", "AEP",
                    "SRE", "EXC", "XEL", "WEC", "ED", "CEG",
                ],
                key_etfs=["XLU", "VPU", "IDU"],
                competitive_dynamics=CompetitiveDynamics.MONOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE],
                margin_profile="operating 20-30%, regulated ROE 9-11%",
                secular_trends=[
                    "grid modernization", "renewable integration",
                    "EV charging infrastructure",
                    "data center power demand (AI)",
                    "rate base growth from electrification",
                ],
                risks=["interest rate sensitivity", "regulatory lag", "wildfire liability"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Independent Power & Renewables",
                position=ValueChainPosition.UPSTREAM,
                description="Non-regulated power generation, renewables operators",
                key_companies=[
                    "CEG", "VST", "NRG", "AES", "CWEN",
                    "BEP", "AY",
                ],
                key_etfs=["ACES", "ICLN"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.COST_ADVANTAGE],
                margin_profile="EBITDA 40-60%",
                secular_trends=[
                    "nuclear power renaissance", "merchant power pricing",
                    "renewable PPAs", "AI data center demand",
                ],
                risks=["power price volatility", "permitting", "technology risk"],
                capex_intensity="high",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Gas & Water Utilities",
                position=ValueChainPosition.INTEGRATED,
                description="Natural gas distribution, water utilities",
                key_companies=[
                    "AWK", "WTRG", "SWX", "NI", "OGS",
                    "ATO", "LNT",
                ],
                key_etfs=["XLU", "FIW"],
                competitive_dynamics=CompetitiveDynamics.MONOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE],
                margin_profile="operating 20-30%",
                secular_trends=[
                    "water infrastructure investment",
                    "gas system safety upgrades",
                ],
                risks=["regulation", "environmental liabilities", "weather"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
        ],
        primary_etfs=["XLU", "VPU", "IDU", "FUTY"],
        preferred_cycle_phases=[
            CyclePhase.LATE_EXPANSION, CyclePhase.RECESSION,
        ],
        beta=0.55,
        weight_in_sp500_pct=2.5,
    )

    # ── REAL ESTATE ───────────────────────────────────────────────
    db[GICSSector.REAL_ESTATE] = SectorProfile(
        sector=GICSSector.REAL_ESTATE,
        value_chain=[
            ValueChainSegment(
                name="Data Center REITs",
                position=ValueChainPosition.ENABLING,
                description="Colocation, hyperscale, edge data centers",
                key_companies=["EQIX", "DLR", "AMT", "CCI", "SBAC"],
                key_etfs=["VNQ", "XLRE"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.SWITCHING_COSTS, MoatType.EFFICIENT_SCALE],
                margin_profile="EBITDA 50-60%, AFFO margins 40-50%",
                secular_trends=[
                    "AI/cloud compute demand", "edge computing",
                    "5G infrastructure", "sovereign data requirements",
                ],
                risks=["power availability", "capex intensity", "interest rates"],
                capex_intensity="high",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Industrial & Logistics REITs",
                position=ValueChainPosition.MIDSTREAM,
                description="Warehouses, distribution centers, cold storage",
                key_companies=["PLD", "REXR", "STAG", "EGP", "FR"],
                key_etfs=["VNQ", "XLRE"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.COST_ADVANTAGE],
                margin_profile="NOI margins 70-80%",
                secular_trends=[
                    "e-commerce fulfillment", "nearshoring",
                    "cold storage demand", "last-mile logistics",
                ],
                risks=["supply additions", "interest rates", "rent growth deceleration"],
                capex_intensity="medium",
                regulatory_exposure="low",
            ),
            ValueChainSegment(
                name="Residential REITs",
                position=ValueChainPosition.DOWNSTREAM,
                description="Apartments, single-family rental, manufactured housing",
                key_companies=[
                    "EQR", "AVB", "INVH", "AMH", "MAA",
                    "UDR", "CPT", "SUI", "ELS",
                ],
                key_etfs=["REZ", "VNQ"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.EFFICIENT_SCALE],
                margin_profile="NOI margins 60-70%",
                secular_trends=[
                    "housing affordability pushing rental demand",
                    "single-family rental institutionalization",
                    "Sun Belt migration",
                ],
                risks=["rent control regulation", "supply wave", "interest rates"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Specialty & Other REITs",
                position=ValueChainPosition.INTEGRATED,
                description="Healthcare, self-storage, gaming, timber, retail",
                key_companies=[
                    "PSA", "EXR", "CUBE", "WELL", "VTR",
                    "SPG", "O", "VICI", "WPC", "RYN",
                ],
                key_etfs=["VNQ", "XLRE", "SRVR"],
                competitive_dynamics=CompetitiveDynamics.FRAGMENTED,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.SWITCHING_COSTS],
                margin_profile="NOI 60-80% depending on type",
                secular_trends=[
                    "senior housing demand", "self-storage resilience",
                    "triple-net lease growth", "gaming REIT conversions",
                ],
                risks=["interest rate sensitivity", "tenant concentration", "obsolescence"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
        ],
        primary_etfs=["VNQ", "XLRE", "IYR", "FREL", "SCHH"],
        preferred_cycle_phases=[
            CyclePhase.RECOVERY, CyclePhase.EARLY_EXPANSION,
        ],
        beta=0.85,
        weight_in_sp500_pct=2.5,
    )

    # ── COMMUNICATION SERVICES ────────────────────────────────────
    db[GICSSector.COMMUNICATION_SERVICES] = SectorProfile(
        sector=GICSSector.COMMUNICATION_SERVICES,
        value_chain=[
            ValueChainSegment(
                name="Interactive Media & Digital Advertising",
                position=ValueChainPosition.DOWNSTREAM,
                description="Search, social media, digital ad platforms, streaming",
                key_companies=[
                    "GOOGL", "META", "SNAP", "PINS", "TTD",
                    "ROKU", "SPOT", "RDDT",
                ],
                key_etfs=["XLC", "VOX", "SOCL"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.NETWORK_EFFECTS, MoatType.INTANGIBLE_ASSETS],
                margin_profile="gross 55-80%, operating 25-40%",
                secular_trends=[
                    "digital ad spend shift from linear TV",
                    "AI-powered ad targeting", "short-form video",
                    "connected TV", "retail media",
                ],
                risks=["privacy regulation", "antitrust", "ad market cyclicality", "AI disruption of search"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
            ValueChainSegment(
                name="Entertainment & Streaming",
                position=ValueChainPosition.DOWNSTREAM,
                description="Studios, streaming platforms, gaming, music",
                key_companies=[
                    "NFLX", "DIS", "WBD", "PARA", "CMCSA",
                    "EA", "TTWO", "RBLX", "U",
                ],
                key_etfs=["XLC", "HERO", "ESPO"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.INTANGIBLE_ASSETS, MoatType.NETWORK_EFFECTS],
                margin_profile="gross 40-65%, operating 10-25%",
                secular_trends=[
                    "streaming maturation / profitability focus",
                    "gaming as dominant entertainment",
                    "AI in content creation", "live events / sports",
                ],
                risks=["content cost inflation", "subscriber saturation", "strikes / labor"],
                capex_intensity="medium",
                regulatory_exposure="medium",
            ),
            ValueChainSegment(
                name="Telecom Infrastructure",
                position=ValueChainPosition.UPSTREAM,
                description="Wireless carriers, fiber, cable, tower companies",
                key_companies=[
                    "T", "VZ", "TMUS", "CHTR", "CMCSA",
                    "AMT", "CCI", "SBAC", "LUMN",
                ],
                key_etfs=["IYZ", "VOX", "FCOM"],
                competitive_dynamics=CompetitiveDynamics.OLIGOPOLY,
                primary_moats=[MoatType.EFFICIENT_SCALE, MoatType.SWITCHING_COSTS],
                margin_profile="EBITDA 35-45%, capex-heavy",
                secular_trends=[
                    "5G monetization", "fiber-to-home",
                    "fixed wireless access", "private networks",
                ],
                risks=["capex burden", "price competition", "regulation", "cord-cutting"],
                capex_intensity="high",
                regulatory_exposure="high",
            ),
        ],
        primary_etfs=["XLC", "VOX", "FCOM"],
        preferred_cycle_phases=[
            CyclePhase.MID_EXPANSION, CyclePhase.LATE_EXPANSION,
        ],
        beta=1.05,
        weight_in_sp500_pct=8.5,
    )

    return db


# ─── ANALYSIS FUNCTIONS ──────────────────────────────────────────────

def rank_sectors(
    db: dict[GICSSector, SectorProfile],
) -> list[tuple[GICSSector, float, str]]:
    """Rank all sectors by composite score, return (sector, score, verdict)."""
    ranked = [
        (sector, profile.composite_score, profile.investment_verdict)
        for sector, profile in db.items()
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def find_opportunities(
    db: dict[GICSSector, SectorProfile],
    min_structural_score: float = 60,
    preferred_moats: list[MoatType] | None = None,
) -> list[SectorOpportunity]:
    """Scan all sector value chains for investable opportunities."""
    opportunities: list[SectorOpportunity] = []

    for sector, profile in db.items():
        if profile.structural_score.total < min_structural_score:
            continue

        for segment in profile.value_chain:
            if preferred_moats:
                if not any(m in segment.primary_moats for m in preferred_moats):
                    continue

            is_core = (
                profile.structural_score.total >= 70
                and segment.competitive_dynamics
                in (CompetitiveDynamics.OLIGOPOLY, CompetitiveDynamics.MONOPOLY)
            )

            opportunities.append(
                SectorOpportunity(
                    sector=sector,
                    segment=segment.name,
                    thesis=f"{segment.description}. "
                    f"Secular trends: {', '.join(segment.secular_trends[:3])}.",
                    vehicle_type="ETF" if segment.key_etfs else "single_stock",
                    tickers=segment.key_etfs[:3] + segment.key_companies[:5],
                    time_horizon="long_term",
                    conviction="high" if is_core else "medium",
                    catalysts=segment.secular_trends[:3],
                    risks=segment.risks[:3],
                    fit_for_core=is_core,
                    fit_for_satellite=not is_core,
                )
            )

    return opportunities


def get_cycle_favored_sectors(
    db: dict[GICSSector, SectorProfile],
    current_phase: CyclePhase,
) -> list[tuple[GICSSector, SectorProfile]]:
    """Return sectors whose preferred cycle phases include the current one."""
    return [
        (sector, profile)
        for sector, profile in db.items()
        if current_phase in profile.preferred_cycle_phases
    ]


def value_chain_deep_dive(
    profile: SectorProfile,
) -> dict[str, dict]:
    """Decompose a sector into its value chain segments with full analysis."""
    result = {}
    for seg in profile.value_chain:
        result[seg.name] = {
            "position": seg.position.value,
            "competitive_dynamics": seg.competitive_dynamics.value,
            "moats": [m.value for m in seg.primary_moats],
            "margin_profile": seg.margin_profile,
            "capex_intensity": seg.capex_intensity,
            "regulatory_exposure": seg.regulatory_exposure,
            "secular_trends": seg.secular_trends,
            "risks": seg.risks,
            "key_etfs": seg.key_etfs,
            "top_companies": seg.key_companies[:8],
        }
    return result
