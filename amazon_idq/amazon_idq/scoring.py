"""Weighted aggregation of rule findings into a proxy listing-quality score.

IMPORTANT: this is NOT Amazon's IDQ. Amazon's Item Data Quality score and the
Seller Central Listing Quality Dashboard are proprietary, undisclosed, and
category- and quarter-specific. This module produces an auditable proxy whose
weights you are expected to recalibrate against your own listings once you can
observe their real LQD values. Treat the pillar breakdown as the product and
the headline number as a convenience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .findings import Finding, SEVERITY_ORDER
from .models import Listing
from .profiles import get_profile
from .rules import run_rules

# Pillar weights, summing to 100. Edit these; that is the intended knob.
DEFAULT_WEIGHTS: dict[str, float] = {
    "content": 22.0,
    "media": 18.0,
    "keywords": 15.0,
    "attributes": 20.0,
    "compliance": 10.0,
    "advertising": 5.0,
    "customer": 10.0,
}

GRADES = [(90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F")]


@dataclass
class PillarScore:
    pillar: str
    earned: float
    maximum: float
    weight: float

    @property
    def pct(self) -> float:
        return 100.0 * self.earned / self.maximum if self.maximum else 0.0

    @property
    def weighted(self) -> float:
        return self.weight * (self.earned / self.maximum) if self.maximum else 0.0


@dataclass
class ListingScore:
    asin: str
    category: str
    score: float
    grade: str
    pillars: dict[str, PillarScore]
    findings: list[Finding]
    blockers: list[Finding] = field(default_factory=list)

    def top_fixes(self, n: int = 10) -> list[Finding]:
        """Findings ranked by weighted points recoverable, then severity."""
        ranked = [f for f in self.findings if not f.passed and f.fix]
        return sorted(
            ranked,
            key=lambda f: (
                -self._weighted_loss(f),
                SEVERITY_ORDER.get(f.severity, 9),
            ),
        )[:n]

    def _weighted_loss(self, f: Finding) -> float:
        p = self.pillars.get(f.pillar)
        if not p or not p.maximum:
            return f.lost
        return round(f.lost / p.maximum * p.weight, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asin": self.asin,
            "category": self.category,
            "score": self.score,
            "grade": self.grade,
            "disclaimer": "Proxy score. Not Amazon's IDQ or Listing Quality Dashboard value.",
            "pillars": {
                k: {
                    "pct": round(v.pct, 1),
                    "weight": v.weight,
                    "weighted_points": round(v.weighted, 2),
                    "earned": round(v.earned, 2),
                    "maximum": v.maximum,
                }
                for k, v in self.pillars.items()
            },
            "blockers": [f.to_dict() for f in self.blockers],
            "top_fixes": [
                dict(f.to_dict(), weighted_gain=self._weighted_loss(f)) for f in self.top_fixes()
            ],
            "findings": [f.to_dict() for f in self.findings],
        }


def grade_for(score: float) -> str:
    for threshold, letter in GRADES:
        if score >= threshold:
            return letter
    return "F"


def score_listing(listing: Listing, weights: dict[str, float] | None = None) -> ListingScore:
    weights = dict(weights or DEFAULT_WEIGHTS)
    profile = get_profile(listing.category)
    findings = run_rules(listing, profile)

    pillars: dict[str, PillarScore] = {}
    for f in findings:
        p = pillars.get(f.pillar)
        if p is None:
            p = pillars[f.pillar] = PillarScore(f.pillar, 0.0, 0.0, weights.get(f.pillar, 0.0))
        p.earned += f.earned
        p.maximum += f.maximum

    active_weight = sum(p.weight for p in pillars.values())
    raw = sum(p.weighted for p in pillars.values())
    score = round(100.0 * raw / active_weight, 1) if active_weight else 0.0

    blockers = [f for f in findings if f.severity == "critical" and not f.passed]
    return ListingScore(
        asin=listing.asin,
        category=listing.category,
        score=score,
        grade=grade_for(score),
        pillars=pillars,
        findings=findings,
        blockers=blockers,
    )
