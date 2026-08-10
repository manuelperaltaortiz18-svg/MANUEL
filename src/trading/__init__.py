"""
Intraday S&P 500 trading bot — range breakout with a strict 1:1 risk/reward.

Scope note: this package is an execution tool with a horizon of hours. It is
deliberately isolated from the long-term investment system in `src/analysis`,
`src/scoring` and `src/engines`, and its output must never be used to justify
changes to the strategic allocation (CLAUDE.md §2, §42).

Import from the submodules directly, e.g.:

    from src.trading.backtest import run_backtest
    from src.trading.data import load_csv
"""
