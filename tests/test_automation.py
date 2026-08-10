"""End-to-end checks for the Chrome automation cycle."""
from __future__ import annotations

import json

import pytest

from automation.browser import chromium_executable
from automation.dashboard import build_payload, render_dashboard


def test_payload_covers_every_portfolio():
    payload = build_payload()
    keys = {p["key"] for p in payload["portfolios"]}
    assert keys == {"conservadora", "equilibrada", "agresiva"}
    for portfolio in payload["portfolios"]:
        assert portfolio["positions"], "portfolio without positions"
        weight_sum = sum(p["weight"] for p in portfolio["positions"])
        assert abs(weight_sum - 100.0) < 0.01


def test_dashboard_html_is_self_contained():
    html = render_dashboard()
    assert "__PORTFOLIO_DATA__" in html
    # No external resources: the page must render with the network blocked.
    assert "http://" not in html.replace("http://www.w3.org/2000/svg", "")
    assert "https://" not in html


@pytest.mark.skipif(
    chromium_executable() is None, reason="Chromium build not available"
)
def test_browser_cycle_matches_python_engine(tmp_path, monkeypatch):
    pytest.importorskip("playwright.sync_api")
    from automation import run_cycle as cycle

    monkeypatch.setattr(cycle, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(cycle, "SCREENSHOT_DIR", tmp_path / "screenshots")

    result = cycle.run_cycle(headless=True)

    failures = [f"{c.name}: {c.detail}" for c in result.failures]
    assert not failures, failures
    assert not result.console_errors, result.console_errors
    assert len(result.screenshots) == 3

    json_path, md_path = cycle.write_reports(result)
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert md_path.exists()
