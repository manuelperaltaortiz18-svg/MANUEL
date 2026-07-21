"""
System-wide constants for the Long-Term Investment System.
"""

# §1 — Dual Horizon
STRATEGIC_HORIZON_YEARS_MIN = 20
STRATEGIC_HORIZON_YEARS_MAX = 40
TACTICAL_HORIZON_MONTHS_MIN = 3
TACTICAL_HORIZON_MONTHS_MAX = 18
DEFAULT_INVESTMENT_HORIZON_YEARS = 40

# §5 — Historical windows (years)
HISTORICAL_WINDOWS = [20, 15, 10, 5, 3, 1]
SHORT_WINDOWS_MONTHS = [12, 6, 3, 1]

# §7 — Rolling return windows (years)
ROLLING_WINDOWS = [1, 3, 5, 10]

# §13 — Cost thresholds
MAX_CORE_TER_PCT = 0.30
MAX_SATELLITE_TER_PCT = 0.65

# §15 — Core vs Satellite
CORE_MAX_POSITIONS = 8
SATELLITE_MAX_POSITIONS = 12

# §16 — Core rotation penalty multiplier
CORE_ROTATION_PENALTY = 3.0
SATELLITE_ROTATION_PENALTY = 1.0

# §36 — Max tactical deviation from strategic allocation (percentage points)
MAX_TACTICAL_DEVIATION_PP = 15.0

# §51 — Complexity penalty threshold
PORTFOLIO_COMPLEXITY_THRESHOLD = 10

# §53 — Review frequencies
STRATEGIC_REVIEW_MONTHS = 6
TACTICAL_REVIEW_MONTHS = 1

# §31 — Compounding scenario rates
SCENARIO_RATES = {
    "conservative": 0.04,
    "base": 0.06,
    "moderate": 0.08,
    "optimistic": 0.10,
}

# §33–§34 — Spanish tax brackets on capital gains (2024)
SPAIN_TAX_BRACKETS = [
    (6_000, 0.19),
    (50_000, 0.21),
    (200_000, 0.23),
    (300_000, 0.27),
    (float("inf"), 0.28),
]

# §9 — Crisis periods for resilience scoring
CRISIS_PERIODS = {
    "dotcom": ("2000-03-24", "2002-10-09"),
    "gfc": ("2007-10-09", "2009-03-09"),
    "eurozone": ("2011-05-02", "2011-10-04"),
    "covid": ("2020-02-19", "2020-03-23"),
    "inflation_2022": ("2022-01-03", "2022-10-12"),
}

# §41 — Decision hierarchy weights (sum = 1.0)
DECISION_HIERARCHY_WEIGHTS = {
    "long_term_compounding": 0.20,
    "strategic_fit": 0.15,
    "diversification": 0.12,
    "cost_tax_efficiency": 0.12,
    "structural_risk": 0.10,
    "historical_evidence": 0.10,
    "market_regime": 0.07,
    "relative_strength": 0.06,
    "trend": 0.05,
    "short_term_momentum": 0.03,
}

# §40 — Strategic/Tactical matrix thresholds
STRATEGIC_HIGH_THRESHOLD = 70
TACTICAL_HIGH_THRESHOLD = 60
