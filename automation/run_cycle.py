"""
Full browser automation cycle: build → serve → drive Chrome → verify → report.

Run it with:

    python -m automation.run_cycle              # headless
    python -m automation.run_cycle --headed     # visible browser

Every portfolio tab is opened in Chromium, the monthly contribution is
changed through the real input, and the numbers rendered in the DOM are
checked against `src.core.compounding`. The run exits non-zero if any
check fails, so it doubles as an end-to-end test.
"""
from __future__ import annotations

import argparse
import json
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from automation.browser import launch_chromium
from automation.dashboard import HORIZONS, INFLATION, write_dashboard
from src.config.constants import SCENARIO_RATES
from src.config.portfolio_myinvestor import (
    cartera_agresiva,
    cartera_conservadora,
    cartera_equilibrada,
)
from src.core.compounding import future_value, real_future_value

BUILD_DIR = Path("build")
SCREENSHOT_DIR = BUILD_DIR / "screenshots"
TEST_CONTRIBUTION = 300.0
# Float tolerance between the JavaScript and Python compounding loops.
TOLERANCE_EUR = 0.01

PORTFOLIO_BUILDERS = {
    "conservadora": cartera_conservadora,
    "equilibrada": cartera_equilibrada,
    "agresiva": cartera_agresiva,
}


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class CycleResult:
    started_at: str
    checks: list[Check] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    def record(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(Check(name, passed, detail))

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed]

    @property
    def ok(self) -> bool:
        return not self.failures and not self.console_errors


class QuietHandler(SimpleHTTPRequestHandler):
    """Static file handler without per-request logging."""

    def log_message(self, fmt, *args):  # noqa: A002 - signature fixed by stdlib
        pass


@contextmanager
def serve(directory: Path):
    """Serve `directory` on an ephemeral localhost port for the cycle's duration."""
    handler = partial(QuietHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def expected_projections(portfolio, monthly_contribution: float) -> dict[tuple[str, int], dict]:
    """Reference values from the Python engine, keyed by (scenario, years)."""
    expected: dict[tuple[str, int], dict] = {}
    for scenario, gross_rate in SCENARIO_RATES.items():
        net_rate = gross_rate - portfolio.total_ter / 100
        for years in HORIZONS:
            nominal = future_value(
                portfolio.initial_capital, net_rate, years, monthly_contribution
            )
            expected[(scenario, years)] = {
                "nominal": nominal,
                "real": real_future_value(nominal, INFLATION, years),
                "contributions": portfolio.initial_capital
                + monthly_contribution * 12 * years,
            }
    return expected


def read_projection_rows(page) -> dict[tuple[str, int], dict]:
    """Pull the projection numbers straight out of the rendered DOM."""
    rows = page.eval_on_selector_all(
        "#projections-body tr",
        """rows => rows.map(r => ({
            scenario: r.dataset.scenario,
            years: Number(r.dataset.years),
            nominal: Number(r.dataset.nominal),
            real: Number(r.dataset.real),
            contributions: Number(r.dataset.contributions),
        }))""",
    )
    return {(r["scenario"], r["years"]): r for r in rows}


def read_holdings(page) -> list[dict]:
    return page.eval_on_selector_all(
        "#holdings-body tr",
        """rows => rows.map(r => ({
            ticker: r.dataset.ticker,
            weight: Number(r.dataset.weight),
            ter: Number(r.dataset.ter),
            role: r.dataset.role,
        }))""",
    )


def verify_portfolio(page, key: str, result: CycleResult) -> None:
    """Check one portfolio tab: composition, weights, TER and projections."""
    portfolio = PORTFOLIO_BUILDERS[key]()
    label = f"[{key}]"

    holdings = read_holdings(page)
    result.record(
        f"{label} posiciones renderizadas",
        len(holdings) == portfolio.position_count,
        f"DOM {len(holdings)} vs modelo {portfolio.position_count}",
    )

    weight_sum = sum(h["weight"] for h in holdings)
    result.record(
        f"{label} pesos suman 100%",
        abs(weight_sum - 100.0) < 0.01,
        f"suma {weight_sum:.2f}%",
    )

    dom_ter = sum(h["weight"] / 100 * h["ter"] for h in holdings)
    result.record(
        f"{label} TER ponderado coincide",
        abs(dom_ter - portfolio.total_ter) < 1e-6,
        f"DOM {dom_ter:.4f}% vs modelo {portfolio.total_ter:.4f}%",
    )

    # Change the contribution through the real input, as a user would.
    page.fill("#monthly-contribution", str(TEST_CONTRIBUTION))
    page.wait_for_function(
        "() => document.querySelectorAll('#projections-body tr').length > 0"
    )
    result.steps.append(
        f"{label} aportación mensual fijada a {TEST_CONTRIBUTION:.0f} €"
    )

    dom_rows = read_projection_rows(page)
    expected = expected_projections(portfolio, TEST_CONTRIBUTION)
    result.record(
        f"{label} filas de proyección",
        len(dom_rows) == len(expected),
        f"DOM {len(dom_rows)} vs esperado {len(expected)}",
    )

    worst_delta = 0.0
    worst_key = None
    for key_pair, exp in expected.items():
        row = dom_rows.get(key_pair)
        if row is None:
            result.record(f"{label} fila {key_pair} presente", False, "ausente en el DOM")
            continue
        for field_name in ("nominal", "real", "contributions"):
            delta = abs(row[field_name] - exp[field_name])
            if delta > worst_delta:
                worst_delta, worst_key = delta, (key_pair, field_name)

    result.record(
        f"{label} navegador == motor Python",
        worst_delta <= TOLERANCE_EUR,
        f"desviación máx {worst_delta:.4f} € en {worst_key}",
    )


def run_cycle(headless: bool = True) -> CycleResult:
    from playwright.sync_api import sync_playwright

    result = CycleResult(started_at=datetime.now(timezone.utc).isoformat())
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    dashboard = write_dashboard(BUILD_DIR)
    result.steps.append(f"dashboard generado: {dashboard}")

    with serve(BUILD_DIR) as base_url, sync_playwright() as playwright:
        result.steps.append(f"servidor local en {base_url}")
        browser = launch_chromium(playwright, headless=headless)
        result.steps.append(f"Chromium {browser.version} lanzado (headless={headless})")

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on(
            "console",
            lambda msg: result.console_errors.append(msg.text)
            if msg.type == "error"
            else None,
        )
        page.on("pageerror", lambda err: result.console_errors.append(str(err)))

        page.goto(f"{base_url}/dashboard.html", wait_until="load")
        page.wait_for_selector("body[data-rendered='true']")
        result.steps.append("dashboard cargado y renderizado")

        result.record(
            "título de la página",
            "Cartera MyInvestor" in page.title(),
            page.title(),
        )

        for key in PORTFOLIO_BUILDERS:
            page.click(f".tab[data-portfolio='{key}']")
            page.wait_for_selector(f"body[data-active-portfolio='{key}']")
            result.steps.append(f"pestaña '{key}' abierta")

            verify_portfolio(page, key, result)

            shot = SCREENSHOT_DIR / f"{key}.png"
            page.screenshot(path=str(shot), full_page=True)
            result.screenshots.append(str(shot))
            result.steps.append(f"captura guardada: {shot}")

        browser.close()
        result.steps.append("navegador cerrado")

    return result


def write_reports(result: CycleResult) -> tuple[Path, Path]:
    """Persist the run as JSON (machine-readable) and Markdown (human-readable)."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    json_path = BUILD_DIR / "automation_report.json"
    json_path.write_text(
        json.dumps(
            {
                "started_at": result.started_at,
                "ok": result.ok,
                "checks": [vars(c) for c in result.checks],
                "console_errors": result.console_errors,
                "screenshots": result.screenshots,
                "steps": result.steps,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    passed = len(result.checks) - len(result.failures)
    lines = [
        "# Ciclo de automatización en Chrome",
        "",
        f"- Ejecutado: {result.started_at}",
        f"- Resultado: {'OK' if result.ok else 'FALLO'}",
        f"- Comprobaciones: {passed}/{len(result.checks)} superadas",
        f"- Errores de consola: {len(result.console_errors)}",
        "",
        "## Pasos",
        "",
    ]
    lines += [f"{i}. {s}" for i, s in enumerate(result.steps, 1)]
    lines += ["", "## Comprobaciones", "", "| Estado | Comprobación | Detalle |", "|---|---|---|"]
    lines += [
        f"| {'✅' if c.passed else '❌'} | {c.name} | {c.detail} |" for c in result.checks
    ]
    if result.console_errors:
        lines += ["", "## Errores de consola", ""]
        lines += [f"- {e}" for e in result.console_errors]
    lines += ["", "## Capturas", ""]
    lines += [f"- `{s}`" for s in result.screenshots]

    md_path = BUILD_DIR / "automation_report.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--headed", action="store_true", help="lanzar Chrome con ventana visible"
    )
    args = parser.parse_args()

    result = run_cycle(headless=not args.headed)
    json_path, md_path = write_reports(result)

    passed = len(result.checks) - len(result.failures)
    print(f"\nComprobaciones: {passed}/{len(result.checks)}")
    for check in result.failures:
        print(f"  FALLO: {check.name} — {check.detail}")
    for error in result.console_errors:
        print(f"  CONSOLA: {error}")
    print(f"Informes: {json_path} · {md_path}")
    print(f"Capturas: {len(result.screenshots)}")
    print("RESULTADO:", "OK" if result.ok else "FALLO")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
