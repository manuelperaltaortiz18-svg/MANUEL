"""
Cartera personalizada MyInvestor — fondos traspasables (§34).
Basada en investigación exhaustiva de fondos disponibles julio 2026.
"""
from src.models.asset import (
    Asset, Portfolio, PortfolioPosition,
    AssetRole, VehicleType, AccumulationType, HistoryType,
)

# ─── FONDOS INVESTIGADOS ─────────────────────────────────────────────

ISHARES_US_S = Asset(
    ticker="IE000N4ZYX28",
    name="iShares US Index Fund (IE) Class S Acc EUR",
    isin="IE000N4ZYX28",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.CORE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=0.05,
    aum_millions=5000,  # umbrella fund
    inception_date="2025-09",  # class S; underlying fund since 1998
    underlying_index="S&P 500",
    underlying_index_inception="1957-03-04",
    history_type=HistoryType.LIVE_INDEX,
    currency="EUR",
    is_transferable_spain=True,
    tags=["core", "usa", "s&p500", "low-cost", "myinvestor-exclusive"],
)

FIDELITY_EUROPE = Asset(
    ticker="IE00BYX5MD61",
    name="Fidelity MSCI Europe Index Fund P Acc EUR",
    isin="IE00BYX5MD61",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.CORE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=0.10,
    aum_millions=2000,
    inception_date="2018-03",
    underlying_index="MSCI Europe",
    underlying_index_inception="1998-12-31",
    history_type=HistoryType.LIVE_FUND,
    currency="EUR",
    is_transferable_spain=True,
    tags=["core", "europe", "low-cost", "420-stocks"],
)

POLAR_CAPITAL_TECH = Asset(
    ticker="IE00BM95B621",
    name="Polar Capital Global Technology R EUR Acc",
    isin="IE00BM95B621",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.SATELLITE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=1.28,
    aum_millions=18000,
    inception_date="2020-06-30",  # R class; strategy since 2001
    underlying_index="Dow Jones Global Technology NTR",
    underlying_index_inception="1999-01-01",
    history_type=HistoryType.LIVE_FUND,
    currency="EUR",
    is_transferable_spain=True,
    tags=["satellite", "technology", "active", "semiconductors", "ai"],
)

MYINVESTOR_NASDAQ100 = Asset(
    ticker="ES0165265002",
    name="MyInvestor Nasdaq 100 FI",
    isin="ES0165265002",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.SATELLITE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=0.41,
    aum_millions=500,
    inception_date="2023-01",
    underlying_index="Nasdaq-100 NTR EUR",
    underlying_index_inception="1985-01-31",
    history_type=HistoryType.LIVE_INDEX,
    currency="EUR",
    is_transferable_spain=True,  # Spanish domiciled = traspasable
    tags=["satellite", "technology", "nasdaq", "low-cost", "spanish-domiciled"],
)

ASHOKA_INDIA = Asset(
    ticker="IE00BDR0JY05",
    name="Ashoka WhiteOak India Opportunities D EUR Acc",
    isin="IE00BDR0JY05",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.SATELLITE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=0.00,  # performance-fee-only model on class D
    aum_millions=1950,
    inception_date="2018-11",
    underlying_index="MSCI India IMI",
    underlying_index_inception="2007-06-01",
    history_type=HistoryType.LIVE_FUND,
    currency="EUR",
    is_transferable_spain=True,
    tags=["satellite", "india", "active", "performance-fee-only", "alpha"],
)

ISHARES_EM_S = Asset(
    ticker="IE000QAZP7L2",
    name="iShares Emerging Markets Index Fund (IE) Class S Acc EUR",
    isin="IE000QAZP7L2",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.SATELLITE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=0.16,
    aum_millions=3000,
    inception_date="2025-09",  # class S; underlying strategy decades old
    underlying_index="MSCI Emerging Markets",
    underlying_index_inception="1987-12-31",
    history_type=HistoryType.LIVE_INDEX,
    currency="EUR",
    is_transferable_spain=True,
    tags=["satellite", "emerging-markets", "low-cost", "myinvestor-exclusive", "24-countries"],
)

PICTET_CHINA = Asset(
    ticker="LU0625737910",
    name="Pictet China Index P EUR",
    isin="LU0625737910",
    vehicle_type=VehicleType.FUND,
    role=AssetRole.SATELLITE,
    accumulation=AccumulationType.ACCUMULATING,
    ter_pct=0.68,
    aum_millions=572,
    inception_date="2011-10",
    underlying_index="MSCI China",
    underlying_index_inception="1992-12-31",
    history_type=HistoryType.LIVE_FUND,
    currency="EUR",
    is_transferable_spain=True,
    tags=["satellite", "china", "index", "548-holdings"],
)

# ─── FONDOS DESCARTADOS CON MOTIVO ───────────────────────────────────

DESCARTADOS = {
    "Vanguard U.S. 500 (IE0032126645)": "Duplica iShares S&P500 con TER 2x mayor (0.10 vs 0.05)",
    "Allianz China A Shares AT USD (LU1997245177)": "TER 2.30% sin alpha persistente demostrado (§14)",
    "Schroder Greater China (LU0365775922)": "TER 1.84%, microposición 3.5%, en realidad es Greater China no China pura",
    "Pictet China Index P EUR (LU0625737910)": "TER 0.68% vs iShares EM Class S 0.16%; riesgo geopolítico de un solo país; EM diversificado superior a largo plazo (§66)",
}

# ─── CARTERAS ─────────────────────────────────────────────────────────

def cartera_agresiva_consciente() -> Portfolio:
    """Cartera recomendada: 5 fondos, traspasables, TER ponderado ~0.18%."""
    return Portfolio(
        name="Agresiva-Consciente MyInvestor (5 fondos)",
        positions=[
            PortfolioPosition(ISHARES_US_S, weight_pct=35, strategic_weight_pct=35, role=AssetRole.CORE),
            PortfolioPosition(FIDELITY_EUROPE, weight_pct=25, strategic_weight_pct=25, role=AssetRole.CORE),
            PortfolioPosition(POLAR_CAPITAL_TECH, weight_pct=12.5, strategic_weight_pct=12.5, role=AssetRole.SATELLITE),
            PortfolioPosition(ASHOKA_INDIA, weight_pct=12.5, strategic_weight_pct=12.5, role=AssetRole.SATELLITE),
            PortfolioPosition(ISHARES_EM_S, weight_pct=15, strategic_weight_pct=15, role=AssetRole.SATELLITE),
        ],
        initial_capital=3_000,
        monthly_contribution=166.67,
        horizon_years=30,
    )


def cartera_alternativa_nasdaq() -> Portfolio:
    """Alternativa: MyInvestor Nasdaq 100 en lugar de Polar Capital (más barata)."""
    return Portfolio(
        name="Alternativa Nasdaq MyInvestor (5 fondos)",
        positions=[
            PortfolioPosition(ISHARES_US_S, weight_pct=35, strategic_weight_pct=35, role=AssetRole.CORE),
            PortfolioPosition(FIDELITY_EUROPE, weight_pct=25, strategic_weight_pct=25, role=AssetRole.CORE),
            PortfolioPosition(MYINVESTOR_NASDAQ100, weight_pct=12.5, strategic_weight_pct=12.5, role=AssetRole.SATELLITE),
            PortfolioPosition(ASHOKA_INDIA, weight_pct=12.5, strategic_weight_pct=12.5, role=AssetRole.SATELLITE),
            PortfolioPosition(ISHARES_EM_S, weight_pct=15, strategic_weight_pct=15, role=AssetRole.SATELLITE),
        ],
        initial_capital=3_000,
        monthly_contribution=166.67,
        horizon_years=30,
    )
