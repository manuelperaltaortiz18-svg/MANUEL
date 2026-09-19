"""CLI: python -m amazon_idq <listing.json> [--json] [--verbose] [--fail-under N]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import Listing
from .report import render
from .scoring import score_listing


def _load(path: Path) -> list[Listing]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data if isinstance(data, list) else [data]
    return [Listing.from_dict(r) for r in records]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="amazon_idq", description="Audit Amazon listings and emit a proxy quality score.")
    ap.add_argument("path", type=Path, help="JSON file with one listing object or a list of them")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a report")
    ap.add_argument("--verbose", action="store_true", help="include every check, not just failures")
    ap.add_argument("--fail-under", type=float, default=None, help="exit 1 if any listing scores below this")
    args = ap.parse_args(argv)

    if not args.path.exists():
        print(f"error: {args.path} not found", file=sys.stderr)
        return 2

    results = [score_listing(l) for l in _load(args.path)]

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(render(r, verbose=args.verbose))

    if args.fail_under is not None and any(r.score < args.fail_under for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
