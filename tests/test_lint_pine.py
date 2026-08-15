"""
Tests for the Pine linter, and a guard that the shipped scripts stay clean.

Every rule here exists because TradingView rejected the real file: the compiler
is not reachable from this repo, so these checks stand in for it.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lint_pine import lint  # noqa: E402

PINE_DIR = Path(__file__).resolve().parents[1] / "pine"


def write(tmp_path, body: str) -> Path:
    path = tmp_path / "test.pine"
    path.write_text(body, encoding="utf-8")
    return path


def rules(findings) -> set[str]:
    return {f.rule for f in findings}


def test_shipped_pine_scripts_are_clean():
    """The files handed to the user must pass every rule."""
    scripts = sorted(PINE_DIR.glob("*.pine"))
    assert scripts, "expected Pine scripts under pine/"
    for path in scripts:
        assert lint(path) == [], f"{path.name}: {[str(f) for f in lint(path)]}"


def test_a_shorttitle_over_ten_characters_is_flagged(tmp_path):
    path = write(tmp_path, 'strategy(title = "x", shorttitle = "1a VELA 1:1")\n')
    assert "shorttitle" in rules(lint(path))


def test_a_short_enough_shorttitle_passes(tmp_path):
    path = write(tmp_path, 'strategy(title = "x", shorttitle = "VELA1 1:1")\n')
    assert "shorttitle" not in rules(lint(path))


def test_nz_with_a_boolean_default_is_flagged(tmp_path):
    """nz() takes numeric sources; a bool default gives it away."""
    path = write(tmp_path, "newSession = inSession and not nz(inSession[1], false)\n")
    assert "nz-bool" in rules(lint(path))


def test_nz_with_a_numeric_default_is_fine(tmp_path):
    path = write(tmp_path, "value = nz(close[1], 0)\n")
    assert "nz-bool" not in rules(lint(path))


def test_a_wrapped_line_indented_by_four_is_flagged(tmp_path):
    """A multiple of 4 reads as a new block, not as a continuation."""
    path = write(tmp_path, "a = b > 0 and\n    c < 1\n")
    assert "continuation" in rules(lint(path))


def test_a_wrapped_line_indented_by_a_non_multiple_passes(tmp_path):
    path = write(tmp_path, "a = b > 0 and\n     c < 1\n")
    assert "continuation" not in rules(lint(path))


def test_a_function_definition_is_not_treated_as_a_continuation(tmp_path):
    path = write(tmp_path, "sizeFor(risk) =>\n    raw = risk > 0 ? 1 : 0\n    raw\n")
    assert "continuation" not in rules(lint(path))


def test_tabs_are_flagged(tmp_path):
    path = write(tmp_path, "a = 1\n\tb = 2\n")
    assert "tab" in rules(lint(path))


def test_unbalanced_parentheses_are_flagged(tmp_path):
    path = write(tmp_path, "a = math.max(1, 2\n")
    assert "parens" in rules(lint(path))


def test_findings_render_with_file_and_line(tmp_path):
    path = write(tmp_path, "a = b and\n    c\n")
    finding = lint(path)[0]
    assert str(finding).startswith(str(path))
    assert ":2:" in str(finding)
