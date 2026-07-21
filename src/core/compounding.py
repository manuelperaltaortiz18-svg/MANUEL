"""
§3, §11, §12, §30, §31, §32 — Compounding calculations.
"""
from __future__ import annotations
from dataclasses import dataclass
from src.config.constants import SCENARIO_RATES, SPAIN_TAX_BRACKETS


@dataclass
class CompoundingResult:
    future_value_nominal: float
    future_value_real: float
    total_contributions: float
    investment_gains: float
    cagr_nominal: float
    cagr_real: float
    net_cagr_after_costs: float
    wealth_multiple: float


def future_value(
    principal: float,
    annual_rate: float,
    years: int,
    monthly_contribution: float = 0.0,
    annual_contribution_growth_pct: float = 0.0,
) -> float:
    """§3 — Compound growth with optional growing contributions."""
    balance = principal
    monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
    contrib = monthly_contribution
    for year in range(years):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + contrib
        contrib *= 1 + annual_contribution_growth_pct / 100
    return balance


def real_future_value(
    nominal_fv: float,
    inflation_rate: float,
    years: int,
) -> float:
    """§11 — Deflate nominal to real."""
    return nominal_fv / (1 + inflation_rate) ** years


def cost_drag(
    principal: float,
    gross_rate: float,
    ter_pct: float,
    years: int,
) -> float:
    """§12 — Wealth lost to fees over time."""
    fv_gross = principal * (1 + gross_rate) ** years
    fv_net = principal * (1 + gross_rate - ter_pct / 100) ** years
    return fv_gross - fv_net


def cost_drag_table(
    principal: float,
    gross_rate: float,
    ter_pct: float,
) -> dict[int, float]:
    """§12 — Cost drag at 10/20/30/40 years."""
    return {y: cost_drag(principal, gross_rate, ter_pct, y) for y in [10, 20, 30, 40]}


def one_pct_matters(
    principal: float,
    base_rate: float,
    years: int = 40,
) -> dict[str, float]:
    """§32 — Impact of ±0.5/1/2% return difference over horizon."""
    base_fv = principal * (1 + base_rate) ** years
    return {
        f"{delta:+.1%}": principal * (1 + base_rate + delta) ** years - base_fv
        for delta in [-0.02, -0.01, -0.005, 0.005, 0.01, 0.02]
    }


def compounding_scenarios(
    principal: float,
    monthly_contribution: float = 0.0,
    annual_contribution_growth_pct: float = 0.0,
    inflation: float = 0.02,
    ter_pct: float = 0.0,
) -> dict[str, dict[int, CompoundingResult]]:
    """§31 — Multi-scenario wealth projections."""
    results: dict[str, dict[int, CompoundingResult]] = {}
    horizons = [10, 20, 30, 40]

    for scenario_name, gross_rate in SCENARIO_RATES.items():
        net_rate = gross_rate - ter_pct / 100
        scenario: dict[int, CompoundingResult] = {}
        for y in horizons:
            fv_nom = future_value(principal, net_rate, y, monthly_contribution, annual_contribution_growth_pct)
            fv_real = real_future_value(fv_nom, inflation, y)

            total_contrib = principal
            c = monthly_contribution
            for yr in range(y):
                total_contrib += c * 12
                c *= 1 + annual_contribution_growth_pct / 100

            gains = fv_nom - total_contrib
            cagr_nom = (fv_nom / principal) ** (1 / y) - 1 if principal > 0 else 0
            cagr_real = cagr_nom - inflation
            wm = fv_nom / principal if principal > 0 else 0

            scenario[y] = CompoundingResult(
                future_value_nominal=round(fv_nom, 2),
                future_value_real=round(fv_real, 2),
                total_contributions=round(total_contrib, 2),
                investment_gains=round(gains, 2),
                cagr_nominal=round(cagr_nom, 4),
                cagr_real=round(cagr_real, 4),
                net_cagr_after_costs=round(net_rate, 4),
                wealth_multiple=round(wm, 2),
            )
        results[scenario_name] = scenario
    return results


def spain_capital_gains_tax(gain: float) -> float:
    """§33 — Spanish progressive capital gains tax."""
    if gain <= 0:
        return 0.0
    tax = 0.0
    remaining = gain
    prev_limit = 0.0
    for limit, rate in SPAIN_TAX_BRACKETS:
        bracket_size = min(remaining, limit - prev_limit)
        if bracket_size <= 0:
            break
        tax += bracket_size * rate
        remaining -= bracket_size
        prev_limit = limit
    return round(tax, 2)


def after_tax_compounded_wealth(
    principal: float,
    annual_rate: float,
    years: int,
    realization_frequency_years: int = 0,
) -> dict[str, float]:
    """§33 — Compare buy-and-hold vs periodic realization tax drag."""
    fv_hold = principal * (1 + annual_rate) ** years
    gain_hold = fv_hold - principal
    tax_hold = spain_capital_gains_tax(gain_hold)
    net_hold = fv_hold - tax_hold

    if realization_frequency_years <= 0 or realization_frequency_years >= years:
        return {"pre_tax": round(fv_hold, 2), "after_tax_hold": round(net_hold, 2)}

    balance = principal
    cost_basis = principal
    periods = years // realization_frequency_years
    for _ in range(periods):
        balance *= (1 + annual_rate) ** realization_frequency_years
        gain = balance - cost_basis
        tax = spain_capital_gains_tax(gain)
        balance -= tax
        cost_basis = balance

    remaining = years % realization_frequency_years
    if remaining > 0:
        balance *= (1 + annual_rate) ** remaining

    final_gain = balance - cost_basis
    final_tax = spain_capital_gains_tax(final_gain)
    net_periodic = balance - final_tax

    return {
        "pre_tax": round(fv_hold, 2),
        "after_tax_hold": round(net_hold, 2),
        "after_tax_periodic": round(net_periodic, 2),
        "tax_drag": round(net_hold - net_periodic, 2),
    }
