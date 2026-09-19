"""Terminal report. Kept dependency-free so it runs anywhere, VS Code included."""

from __future__ import annotations

from .scoring import ListingScore

BAR_WIDTH = 24
ICON = {"critical": "[X]", "high": "[!]", "medium": "[~]", "low": "[.]", "pass": "[v]"}


def _bar(pct: float) -> str:
    filled = int(round(pct / 100 * BAR_WIDTH))
    return "#" * filled + "-" * (BAR_WIDTH - filled)


def render(result: ListingScore, verbose: bool = False) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append(f" LISTING QUALITY AUDIT  ASIN {result.asin}  ({result.category})")
    lines.append("=" * 72)
    lines.append(f" Proxy score: {result.score:.1f}/100    Grade: {result.grade}")
    lines.append(" Proxy metric - not Amazon's IDQ / Listing Quality Dashboard value.")
    lines.append("")

    lines.append(" PILLARS")
    for name, p in sorted(result.pillars.items(), key=lambda kv: -kv[1].weight):
        lines.append(f"  {name:<12} {_bar(p.pct)} {p.pct:5.1f}%  "
                     f"({p.weighted:.1f}/{p.weight:.0f} pts)")
    lines.append("")

    if result.blockers:
        lines.append(f" BLOCKERS ({len(result.blockers)}) - suppression / policy risk")
        for f in result.blockers:
            lines.append(f"  [X] {f.code}: {f.message}")
            if f.fix:
                lines.append(f"      -> {f.fix}")
        lines.append("")

    fixes = result.top_fixes()
    if fixes:
        lines.append(" TOP FIXES BY POINTS RECOVERABLE")
        for i, f in enumerate(fixes, 1):
            gain = result._weighted_loss(f)
            lines.append(f"  {i:>2}. {ICON.get(f.severity,'[?]')} +{gain:4.1f} pts  {f.code}")
            lines.append(f"      {f.message}")
            lines.append(f"      -> {f.fix}")
        lines.append("")

    if verbose:
        lines.append(" ALL CHECKS")
        for f in result.findings:
            lines.append(f"  {ICON.get(f.severity,'[?]')} {f.code:<26} "
                         f"{f.earned:5.1f}/{f.maximum:<5.1f} {f.message}")
        lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)
