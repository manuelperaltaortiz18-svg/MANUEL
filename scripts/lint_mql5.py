#!/usr/bin/env python3
"""
Static checks for MQL5 sources.

MetaEditor is Windows-only, so these files cannot be compiled from here. The
same reasoning as `lint_pine.py`: encode the mistakes that this blindness
produces rather than trusting a read-through.

    python scripts/lint_mql5.py mql5/*.mq5
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_HANDLERS = ("OnInit", "OnTick")
# Constructs that only exist in Pine — a sign the port was left half-done.
PINE_LEFTOVERS = (
    (re.compile(r"\bstrategy\.\w+"), "Pine `strategy.*` call"),
    (re.compile(r"\bta\.\w+"), "Pine `ta.*` call"),
    (re.compile(r"\bmath\.\w+"), "Pine `math.*` call (MQL5 uses MathXxx)"),
    (re.compile(r"\bna\s*\("), "Pine `na()` check"),
    (re.compile(r"\binput\.\w+"), "Pine `input.*` declaration"),
    (re.compile(r":="), "Pine assignment operator"),
)
INPUT_DECL = re.compile(r"^\s*(?:input|sinput)\s+(?:group\s+)?[\w<>]+\s+(\w+)\s*=")
FUNC_DEF = re.compile(r"^[\w:<>\*&\s]+?\b(\w+)\s*\([^;]*\)\s*$")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def strip_comments_and_strings(text: str) -> str:
    """Remove // and /* */ comments and string literals before counting."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        two = text[i : i + 2]
        if two == "//":
            end = text.find("\n", i)
            i = n if end == -1 else end
        elif two == "/*":
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        elif text[i] in "\"'":
            quote = text[i]
            i += 1
            while i < n and text[i] != quote:
                i += 2 if text[i] == "\\" else 1
            i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def lint(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    name = str(path)
    code = strip_comments_and_strings(text)

    for opener, closer, label in (("{", "}", "braces"), ("(", ")", "parentheses"),
                                  ("[", "]", "brackets")):
        if code.count(opener) != code.count(closer):
            findings.append(
                Finding(
                    name,
                    0,
                    "balance",
                    f"unbalanced {label}: {code.count(opener)} {opener} vs "
                    f"{code.count(closer)} {closer}",
                )
            )

    for handler in REQUIRED_HANDLERS:
        if not re.search(rf"\b(?:int|void|double)\s+{handler}\s*\(", code):
            findings.append(
                Finding(name, 0, "handler", f"{handler}() is missing")
            )

    for number, line in enumerate(lines, start=1):
        stripped = line.split("//")[0]
        for pattern, label in PINE_LEFTOVERS:
            if pattern.search(stripped):
                findings.append(
                    Finding(name, number, "pine-leftover", f"{label} left in MQL5 source")
                )

    # An input nobody reads is a promise the code does not keep.
    declared: dict[str, int] = {}
    for number, line in enumerate(lines, start=1):
        match = INPUT_DECL.match(line)
        if match:
            declared[match.group(1)] = number
    for variable, number in declared.items():
        uses = len(re.findall(rf"\b{re.escape(variable)}\b", code))
        if uses <= 1:
            findings.append(
                Finding(name, number, "dead-input", f"input {variable} is never used")
            )

    if "#property" not in text:
        findings.append(Finding(name, 0, "property", "no #property header"))

    return findings


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] or sorted(Path("mql5").glob("*.mq*"))
    if not paths:
        print("No MQL5 files given or found under mql5/", file=sys.stderr)
        return 1

    findings: list[Finding] = []
    for path in paths:
        if not path.exists():
            print(f"{path}: not found", file=sys.stderr)
            return 1
        findings.extend(lint(path))

    for finding in findings:
        print(finding)
    print(f"\n{len(paths)} file(s) checked, {len(findings)} finding(s).", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
