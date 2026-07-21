"""
§31, §37 — Report generation for compounding scenarios and portfolio reviews.
"""
from __future__ import annotations
from src.core.compounding import CompoundingResult


def format_currency(value: float) -> str:
    return f"{value:,.2f} €"


def compounding_report(
    scenarios: dict[str, dict[int, CompoundingResult]],
    principal: float,
) -> str:
    lines = [
        "=" * 80,
        "LONG-TERM COMPOUNDING PROJECTION",
        f"Initial Capital: {format_currency(principal)}",
        "=" * 80,
    ]

    for scenario_name, horizons in scenarios.items():
        lines.append(f"\n--- {scenario_name.upper()} SCENARIO ---")
        for years, result in sorted(horizons.items()):
            lines.extend([
                f"  {years}Y: Nominal {format_currency(result.future_value_nominal)} | "
                f"Real {format_currency(result.future_value_real)} | "
                f"CAGR {result.cagr_nominal:.2%} | "
                f"Real CAGR {result.cagr_real:.2%} | "
                f"Wealth Multiple {result.wealth_multiple:.1f}x",
            ])

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def cost_drag_report(
    principal: float,
    gross_rate: float,
    options: dict[str, float],
) -> str:
    from src.core.compounding import cost_drag_table

    lines = [
        "=" * 80,
        "LONG-TERM COST DRAG ANALYSIS",
        f"Principal: {format_currency(principal)} | Gross Return: {gross_rate:.1%}",
        "=" * 80,
    ]

    for label, ter in sorted(options.items(), key=lambda x: x[1]):
        drags = cost_drag_table(principal, gross_rate, ter)
        lines.append(f"\n  {label} (TER {ter:.2f}%):")
        for y, drag in sorted(drags.items()):
            lines.append(f"    {y}Y cost drag: {format_currency(drag)}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def decision_report(decisions: list) -> str:
    lines = [
        "=" * 80,
        "INVESTMENT DECISION SUMMARY",
        "=" * 80,
    ]
    for d in decisions:
        lines.extend([
            f"\n  {d.ticker}",
            f"    Action: {d.action}",
            f"    Strategic: {d.strategic_score:.0f} | Tactical: {d.tactical_score:.0f}",
            f"    Matrix: {d.matrix_signal}",
            f"    5Y Test: {'PASS' if d.passes_five_year_test else 'FAIL'} | "
            f"Compounding: {'OK' if d.passes_compounding_test else 'RISK'}",
            f"    {d.long_term_impact}",
        ])
    lines.append("\n" + "=" * 80)
    return "\n".join(lines)
