#!/usr/bin/env python3
"""
Static checks for Pine Script files.

The Pine compiler lives inside TradingView, so these scripts cannot be built
from here. This catches the specific mistakes that class of blindness produces
— every rule below was added after a real compile error, not invented.

    python scripts/lint_pine.py pine/*.pine
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_SHORTTITLE = 10

# A wrapped expression continues the previous line. Pine tells a continuation
# apart from a new block by its indentation: a multiple of 4 spaces starts a
# block, anything else continues the line. Getting this wrong reads as
# "end of line without line continuation".
CONTINUATION_ENDINGS = (
    " and", " or", " not", " +", " -", " *", " /", " %",
    " ?", " :", ",", " ==", " !=", " <", " >", " <=", " >=", ":=", "=",
)

# nz() only accepts numeric sources. A bool default proves the source is a
# bool, which the compiler rejects with a "simple int is expected" error.
NZ_BOOL = re.compile(r"\bnz\s*\([^()]*,\s*(true|false)\s*\)")

SHORTTITLE = re.compile(r"""shorttitle\s*=\s*["']([^"']*)["']""")
TAB = re.compile(r"\t")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def _is_continuation_target(previous: str) -> bool:
    """True when the previous line clearly expects the expression to continue."""
    stripped = previous.rstrip()
    if not stripped or stripped.lstrip().startswith("//"):
        return False
    if stripped.endswith("=>"):
        return False  # function definitions open a block on purpose
    return stripped.endswith(CONTINUATION_ENDINGS)


def lint(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    name = str(path)

    for number, line in enumerate(lines, start=1):
        if TAB.search(line):
            findings.append(
                Finding(name, number, "tab", "Pine rejects tabs; use spaces")
            )

        match = SHORTTITLE.search(line)
        if match and len(match.group(1)) > MAX_SHORTTITLE:
            findings.append(
                Finding(
                    name,
                    number,
                    "shorttitle",
                    f"{len(match.group(1))} characters, the limit is {MAX_SHORTTITLE}: "
                    f"{match.group(1)!r}",
                )
            )

        if NZ_BOOL.search(line):
            findings.append(
                Finding(
                    name,
                    number,
                    "nz-bool",
                    "nz() takes numeric sources only; track the previous bool in a "
                    "`var bool` instead",
                )
            )

        if number > 1 and _is_continuation_target(lines[number - 2]):
            indent = len(line) - len(line.lstrip())
            if line.strip() and indent % 4 == 0:
                findings.append(
                    Finding(
                        name,
                        number,
                        "continuation",
                        f"wrapped line indented {indent} spaces (a multiple of 4 reads "
                        "as a new block); use any other indent",
                    )
                )

    if text.count("(") != text.count(")"):
        findings.append(
            Finding(name, 0, "parens", "unbalanced parentheses in the file")
        )
    return findings


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] or sorted(Path("pine").glob("*.pine"))
    if not paths:
        print("No Pine files given or found under pine/", file=sys.stderr)
        return 1

    findings: list[Finding] = []
    for path in paths:
        if not path.exists():
            print(f"{path}: not found", file=sys.stderr)
            return 1
        findings.extend(lint(path))

    for finding in findings:
        print(finding)
    print(
        f"\n{len(paths)} file(s) checked, {len(findings)} finding(s).",
        file=sys.stderr,
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
