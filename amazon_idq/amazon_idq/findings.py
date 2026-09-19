from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "pass": 4}


@dataclass
class Finding:
    pillar: str
    code: str
    earned: float
    maximum: float
    severity: str          # critical | high | medium | low | pass
    message: str
    fix: str = ""

    @property
    def lost(self) -> float:
        return round(self.maximum - self.earned, 3)

    @property
    def passed(self) -> bool:
        return self.earned >= self.maximum

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["lost"] = self.lost
        return d
