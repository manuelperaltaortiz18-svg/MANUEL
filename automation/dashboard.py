"""
Builds the self-contained HTML dashboard that the browser cycle drives.

The page recomputes projections in JavaScript from the embedded portfolio
data, mirroring `src.core.compounding.future_value`. That duplication is
deliberate: the automation cycle compares the browser's numbers against the
Python engine, so a divergence in either implementation fails the run.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config.constants import SCENARIO_RATES
from src.config.portfolio_myinvestor import (
    cartera_agresiva,
    cartera_conservadora,
    cartera_equilibrada,
)
from src.models.asset import Portfolio

HORIZONS = [10, 20, 30, 40]
INFLATION = 0.02

PORTFOLIO_BUILDERS = {
    "conservadora": cartera_conservadora,
    "equilibrada": cartera_equilibrada,
    "agresiva": cartera_agresiva,
}


def portfolio_payload(key: str, portfolio: Portfolio) -> dict:
    """Serialize a Portfolio into the JSON the page consumes."""
    return {
        "key": key,
        "name": portfolio.name,
        "initialCapital": portfolio.initial_capital,
        "monthlyContribution": portfolio.monthly_contribution,
        "horizonYears": portfolio.horizon_years,
        "totalTer": round(portfolio.total_ter, 4),
        "positionCount": portfolio.position_count,
        "positions": [
            {
                "ticker": p.asset.ticker,
                "name": p.asset.name,
                "isin": p.asset.isin,
                "role": p.role.value,
                "weight": p.weight_pct,
                "strategicWeight": p.strategic_weight_pct,
                "ter": p.asset.ter_pct,
                "index": p.asset.underlying_index,
                "transferable": p.asset.is_transferable_spain,
            }
            for p in portfolio.positions
        ],
    }


def build_payload() -> dict:
    """Full data payload: every portfolio plus the shared assumptions."""
    return {
        "scenarioRates": dict(SCENARIO_RATES),
        "horizons": HORIZONS,
        "inflation": INFLATION,
        "portfolios": [
            portfolio_payload(key, builder())
            for key, builder in PORTFOLIO_BUILDERS.items()
        ],
    }


CSS = """
:root {
  color-scheme: light dark;
  --bg: #ffffff; --fg: #16181d; --muted: #5c6270;
  --line: #e3e6ec; --panel: #f7f8fa; --accent: #2f5fd0;
}
@media (prefers-color-scheme: dark) {
  :root { --bg:#14161a; --fg:#e9ecf1; --muted:#a0a7b4;
          --line:#2a2e36; --panel:#1b1e24; --accent:#7aa2f7; }
}
* { box-sizing: border-box; }
body { margin:0; padding:32px; background:var(--bg); color:var(--fg);
       font:15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
h1 { font-size:22px; margin:0 0 4px; }
.sub { color:var(--muted); margin:0 0 24px; font-size:14px; }
.tabs { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
.tab { padding:8px 16px; border:1px solid var(--line); border-radius:999px;
       background:var(--panel); color:var(--fg); cursor:pointer; font:inherit; }
.tab[aria-selected="true"] { background:var(--accent); border-color:var(--accent); color:#fff; }
.controls { display:flex; gap:20px; align-items:flex-end; flex-wrap:wrap;
            padding:16px; border:1px solid var(--line); border-radius:10px;
            background:var(--panel); margin-bottom:24px; }
label { display:block; font-size:12px; text-transform:uppercase;
        letter-spacing:.04em; color:var(--muted); margin-bottom:6px; }
input { padding:8px 10px; border:1px solid var(--line); border-radius:8px;
        background:var(--bg); color:var(--fg); font:inherit; width:150px; }
.stats { display:flex; gap:28px; flex-wrap:wrap; margin-bottom:24px; }
.stat-value { font-size:24px; font-weight:600; }
.stat-label { font-size:12px; text-transform:uppercase;
              letter-spacing:.04em; color:var(--muted); }
h2 { font-size:15px; text-transform:uppercase; letter-spacing:.05em;
     color:var(--muted); margin:28px 0 10px; }
.scroll { overflow-x:auto; }
table { border-collapse:collapse; width:100%; min-width:640px; font-size:14px; }
th, td { text-align:right; padding:9px 12px; border-bottom:1px solid var(--line); }
th:first-child, td:first-child { text-align:left; }
th { font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
.tag { font-size:11px; padding:2px 8px; border-radius:999px;
       border:1px solid var(--line); color:var(--muted); }
"""

JS = """
const DATA = window.__PORTFOLIO_DATA__;
const fmtEur = new Intl.NumberFormat('es-ES',
  { style:'currency', currency:'EUR', maximumFractionDigits:0 });

// Mirror of src.core.compounding.future_value — monthly compounding,
// contribution applied at the end of each month.
function futureValue(principal, annualRate, years, monthlyContribution) {
  let balance = principal;
  const monthlyRate = Math.pow(1 + annualRate, 1 / 12) - 1;
  for (let y = 0; y < years; y++) {
    for (let m = 0; m < 12; m++) {
      balance = balance * (1 + monthlyRate) + monthlyContribution;
    }
  }
  return balance;
}

function project(portfolio, monthlyContribution) {
  const rows = [];
  for (const [scenario, grossRate] of Object.entries(DATA.scenarioRates)) {
    const netRate = grossRate - portfolio.totalTer / 100;
    for (const years of DATA.horizons) {
      const nominal = futureValue(
        portfolio.initialCapital, netRate, years, monthlyContribution);
      const real = nominal / Math.pow(1 + DATA.inflation, years);
      const contributions =
        portfolio.initialCapital + monthlyContribution * 12 * years;
      rows.push({ scenario, years, netRate, nominal, real, contributions,
                  gains: nominal - contributions,
                  multiple: nominal / portfolio.initialCapital });
    }
  }
  return rows;
}

let activeKey = DATA.portfolios[0].key;

function activePortfolio() {
  return DATA.portfolios.find(p => p.key === activeKey);
}

function renderTabs() {
  const host = document.getElementById('tabs');
  host.innerHTML = '';
  for (const p of DATA.portfolios) {
    const btn = document.createElement('button');
    btn.className = 'tab';
    btn.type = 'button';
    btn.dataset.portfolio = p.key;
    btn.setAttribute('role', 'tab');
    btn.setAttribute('aria-selected', String(p.key === activeKey));
    btn.textContent = p.name;
    btn.addEventListener('click', () => {
      activeKey = p.key;
      const input = document.getElementById('monthly-contribution');
      input.value = activePortfolio().monthlyContribution.toFixed(2);
      render();
    });
    host.appendChild(btn);
  }
}

function renderStats(portfolio, contribution) {
  const weightSum = portfolio.positions.reduce((s, p) => s + p.weight, 0);
  const setStat = (id, value, raw) => {
    const el = document.getElementById(id);
    el.textContent = value;
    el.dataset.value = raw;
  };
  setStat('stat-ter', portfolio.totalTer.toFixed(3) + ' %', portfolio.totalTer);
  setStat('stat-positions', String(portfolio.positionCount), portfolio.positionCount);
  setStat('stat-weight', weightSum.toFixed(1) + ' %', weightSum);
  setStat('stat-contribution', fmtEur.format(contribution) + ' /mes', contribution);
}

function renderHoldings(portfolio) {
  const body = document.getElementById('holdings-body');
  body.innerHTML = '';
  for (const pos of portfolio.positions) {
    const tr = document.createElement('tr');
    tr.dataset.ticker = pos.ticker;
    tr.dataset.weight = pos.weight;
    tr.dataset.ter = pos.ter;
    tr.dataset.role = pos.role;
    tr.innerHTML = `
      <td>${pos.name}<br><span class="tag">${pos.isin}</span></td>
      <td>${pos.index ?? '—'}</td>
      <td><span class="tag">${pos.role}</span></td>
      <td>${pos.weight.toFixed(1)} %</td>
      <td>${pos.ter.toFixed(2)} %</td>
      <td>${pos.transferable ? 'Sí' : 'No'}</td>`;
    body.appendChild(tr);
  }
}

function renderProjections(portfolio, contribution) {
  const body = document.getElementById('projections-body');
  body.innerHTML = '';
  for (const row of project(portfolio, contribution)) {
    const tr = document.createElement('tr');
    tr.dataset.scenario = row.scenario;
    tr.dataset.years = row.years;
    tr.dataset.nominal = row.nominal.toFixed(2);
    tr.dataset.real = row.real.toFixed(2);
    tr.dataset.contributions = row.contributions.toFixed(2);
    tr.innerHTML = `
      <td>${row.scenario}</td>
      <td>${row.years} años</td>
      <td>${(row.netRate * 100).toFixed(2)} %</td>
      <td>${fmtEur.format(row.contributions)}</td>
      <td>${fmtEur.format(row.nominal)}</td>
      <td>${fmtEur.format(row.real)}</td>
      <td>${row.multiple.toFixed(1)}x</td>`;
    body.appendChild(tr);
  }
}

function render() {
  const portfolio = activePortfolio();
  const contribution = parseFloat(
    document.getElementById('monthly-contribution').value) || 0;
  document.getElementById('portfolio-name').textContent = portfolio.name;
  renderTabs();
  renderStats(portfolio, contribution);
  renderHoldings(portfolio);
  renderProjections(portfolio, contribution);
  document.body.dataset.rendered = 'true';
  document.body.dataset.activePortfolio = portfolio.key;
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('monthly-contribution');
  input.value = activePortfolio().monthlyContribution.toFixed(2);
  input.addEventListener('input', render);
  render();
});
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cartera MyInvestor — Panel de proyecciones</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>%F0%9F%93%88</text></svg>">
<style>{css}</style>
</head>
<body>
<h1 id="portfolio-name">Cargando…</h1>
<p class="sub">Proyecciones de capitalización a largo plazo (§31) · inflación {inflation:.0%} · TER descontado del retorno bruto</p>

<div class="tabs" id="tabs" role="tablist"></div>

<div class="controls">
  <div>
    <label for="monthly-contribution">Aportación mensual (€)</label>
    <input id="monthly-contribution" type="number" min="0" step="10">
  </div>
  <p class="sub" style="margin:0">Cambia la aportación y la tabla se recalcula al instante.</p>
</div>

<div class="stats">
  <div><div class="stat-value" id="stat-ter">—</div><div class="stat-label">TER ponderado</div></div>
  <div><div class="stat-value" id="stat-positions">—</div><div class="stat-label">Posiciones</div></div>
  <div><div class="stat-value" id="stat-weight">—</div><div class="stat-label">Suma de pesos</div></div>
  <div><div class="stat-value" id="stat-contribution">—</div><div class="stat-label">Aportación</div></div>
</div>

<h2>Composición</h2>
<div class="scroll">
<table id="holdings">
  <thead><tr>
    <th>Fondo</th><th>Índice</th><th>Rol</th><th>Peso</th><th>TER</th><th>Traspasable</th>
  </tr></thead>
  <tbody id="holdings-body"></tbody>
</table>
</div>

<h2>Proyecciones</h2>
<div class="scroll">
<table id="projections">
  <thead><tr>
    <th>Escenario</th><th>Horizonte</th><th>CAGR neto</th>
    <th>Aportado</th><th>Valor nominal</th><th>Valor real</th><th>Múltiplo s/ capital inicial</th>
  </tr></thead>
  <tbody id="projections-body"></tbody>
</table>
</div>

<script>window.__PORTFOLIO_DATA__ = {payload};</script>
<script>{js}</script>
</body>
</html>
"""


def render_dashboard() -> str:
    """Return the dashboard HTML as a string."""
    payload = build_payload()
    return HTML_TEMPLATE.format(
        css=CSS,
        js=JS,
        inflation=INFLATION,
        payload=json.dumps(payload, ensure_ascii=False),
    )


def write_dashboard(output_dir: Path) -> Path:
    """Write the dashboard to `output_dir/dashboard.html` and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "dashboard.html"
    path.write_text(render_dashboard(), encoding="utf-8")
    return path


if __name__ == "__main__":
    written = write_dashboard(Path("build"))
    print(f"dashboard written to {written}")
