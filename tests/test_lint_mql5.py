"""
Tests for the MQL5 linter, and a guard that the shipped EA stays clean.

MetaEditor only runs on Windows, so the compiler is out of reach from here;
these checks stand in for the mistakes that blindness produces.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lint_mql5 import lint, strip_comments_and_strings  # noqa: E402

MQL5_DIR = Path(__file__).resolve().parents[1] / "mql5"

MINIMAL = """
#property version "1.00"
input double InpRisk = 1.0;
int OnInit(void) { return 0; }
void OnTick(void) { double x = InpRisk; }
"""


def write(tmp_path, body: str) -> Path:
    path = tmp_path / "test.mq5"
    path.write_text(body, encoding="utf-8")
    return path


def rules(findings) -> set[str]:
    return {f.rule for f in findings}


def test_the_shipped_expert_advisor_is_clean():
    files = sorted(MQL5_DIR.glob("*.mq5"))
    assert files, "expected an EA under mql5/"
    for path in files:
        assert lint(path) == [], f"{path.name}: {[str(f) for f in lint(path)]}"


def test_a_minimal_valid_file_passes(tmp_path):
    assert lint(write(tmp_path, MINIMAL)) == []


def test_unbalanced_braces_are_flagged(tmp_path):
    path = write(tmp_path, MINIMAL + "\nvoid Extra(void) { if(true) { \n")
    assert "balance" in rules(lint(path))


def test_braces_inside_comments_and_strings_do_not_count(tmp_path):
    """The naive count would report a false positive on this file."""
    body = MINIMAL + '\nvoid F(void) { Print("} } {"); /* } */ }\n'
    assert "balance" not in rules(lint(path := write(tmp_path, body)))
    assert lint(path) == []


def test_a_missing_handler_is_flagged(tmp_path):
    path = write(tmp_path, '#property version "1.0"\nvoid OnTick(void) { }\n')
    assert "handler" in rules(lint(path))


@pytest.mark.parametrize(
    "snippet",
    [
        "double x = strategy.equity;",
        "double a = ta.atr(14);",
        "double b = math.max(1, 2);",
        "if(na(x)) return;",
        "input.float(1.0);",
        "x := 5;",
    ],
)
def test_pine_leftovers_are_flagged(tmp_path, snippet):
    path = write(tmp_path, MINIMAL + f"\nvoid F(void) {{ {snippet} }}\n")
    assert "pine-leftover" in rules(lint(path))


def test_pine_words_inside_comments_are_ignored(tmp_path):
    path = write(tmp_path, MINIMAL + "\n// puerto de strategy.entry a MQL5\n")
    assert "pine-leftover" not in rules(lint(path))


def test_an_unused_input_is_flagged(tmp_path):
    path = write(tmp_path, MINIMAL + "\ninput int InpUnused = 3;\n")
    findings = lint(path)
    assert "dead-input" in rules(findings)
    assert any("InpUnused" in f.message for f in findings)


def test_a_used_input_is_not_flagged(tmp_path):
    body = MINIMAL + "\ninput int InpUsed = 3;\nvoid G(void) { int y = InpUsed; }\n"
    assert "dead-input" not in rules(lint(write(tmp_path, body)))


def test_a_missing_property_header_is_flagged(tmp_path):
    path = write(tmp_path, "int OnInit(void) { return 0; }\nvoid OnTick(void) { }\n")
    assert "property" in rules(lint(path))


def test_comment_and_string_stripping():
    assert strip_comments_and_strings('a; // b\nc;') .strip() == "a; \nc;".strip()
    assert "hidden" not in strip_comments_and_strings('Print("hidden");')
    assert "block" not in strip_comments_and_strings("/* block */ code;")
