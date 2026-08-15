#!/usr/bin/env python3
"""
Walk-forward parameter search for the first-candle strategy.

    python scripts/optimize.py --csv data/NAS100_M1.csv --instrument NAS100

Reports every candidate twice — on the data it was tuned on and on data it has
never seen — plus the hit rate the luckiest of N coin-flippers would have shown
over the same number of trades. If the winner cannot beat that, the search
found noise, and the script says so.
"""
from __future__ import annotations

import argparse
import sys
from datetime import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.trading_config import (  # noqa: E402
    INSTRUMENTS,
    BotConfig,
    FirstCandleBreakConfig,
    RiskConfig,
    SessionConfig,
)
from src.trading.backtest import run_backtest  # noqa: E402
from src.trading.data import filter_session, load_csv, resample, synthetic_bars  # noqa: E402
from src.trading.optimize import optimise  # noqa: E402
from src.trading.strategy import FirstCandleBreakStrategy  # noqa: E402


def parse_time(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Walk-forward optimisation")
    p.add_argument("--csv", help="OHLCV file; omit for synthetic data")
    p.add_argument("--timeframe", type=int, default=15)
    p.add_argument("--instrument", default="NAS100", choices=sorted(INSTRUMENTS))
    p.add_argument("--equity", type=float, default=100_000.0)
    p.add_argument("--risk-pct", type=float, default=0.5)
    p.add_argument("--session-start", type=parse_time, default=time(9, 30))
    p.add_argument("--session-end", type=parse_time, default=time(16, 0))
    p.add_argument("--in-sample", type=float, default=0.6, help="Fraction tuned on")
    p.add_argument("--min-trades", type=int, default=20)
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--days", type=int, default=400, help="Synthetic sessions")
    p.add_argument("--seed", type=int, default=5)
    return p


# The grid stays deliberately small. Every extra axis is another chance to fit
# noise, and the chance benchmark grows with it.
GRID = {
    "range_minutes": (15, 30),
    "stop_buffer_ticks": (0.0, 2.0, 8.0),
    "require_excursion": (False, True),
    "max_range_points": (0.0, 150.0),
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    instrument = INSTRUMENTS[args.instrument]
    session = SessionConfig(
        session_start=args.session_start,
        session_end=args.session_end,
        entry_cutoff=time(15, 30),
        flat_at=time(15, 45),
        opening_range_minutes=15,
    )

    if args.csv:
        bars = load_csv(args.csv)
        if args.timeframe > 1:
            bars = resample(bars, args.timeframe)
        source = args.csv
    else:
        bars = synthetic_bars(
            days=args.days, minutes=args.timeframe, start_price=20_000.0,
            bar_volatility_points=18.0, gap_volatility_points=45.0,
            trend_points_per_day=6.0, seed=args.seed, tick_size=instrument.tick_size,
        )
        source = f"synthetic ({args.days} sessions)"
    bars = filter_session(bars, session.session_start, session.session_end)
    if not bars:
        print("No bars inside the session window.", file=sys.stderr)
        return 1

    def evaluate(subset, params):
        strategy_config = FirstCandleBreakConfig(max_signals_per_day=1, **params)
        config = BotConfig(
            instrument=instrument,
            session=session,
            risk=RiskConfig(risk_per_trade_pct=args.risk_pct, max_trades_per_day=1),
            strategy=strategy_config,
            starting_equity=args.equity,
            timeframe_minutes=args.timeframe,
        )
        strategy = FirstCandleBreakStrategy(strategy_config, instrument, session)
        return run_backtest(subset, config, strategy=strategy).report

    outcome = optimise(
        bars, GRID, evaluate,
        in_sample_fraction=args.in_sample,
        min_trades=args.min_trades,
        top=args.top,
        seed=args.seed,
    )

    print()
    print("=" * 88)
    print(f"WALK-FORWARD — {instrument.symbol} {args.timeframe}m — {source}")
    print("=" * 88)
    print(
        f"{outcome.combinations_tested} combinations · "
        f"{outcome.in_sample_sessions} sessions tuned on · "
        f"{outcome.out_sample_sessions} held back"
    )
    print("-" * 88)
    print(f"{'parámetros':<52}{'IS R':>8}{'IS ops':>8}{'OOS R':>8}{'OOS ops':>9}")
    for candidate in outcome.candidates:
        oos = candidate.out_sample
        print(
            f"{candidate.describe():<52}"
            f"{candidate.in_sample_score:>+8.3f}{candidate.in_sample.trades:>8}"
            f"{candidate.out_sample_score:>+8.3f}"
            f"{oos.trades if oos else 0:>9}"
        )

    print("-" * 88)
    if outcome.best:
        best = outcome.best
        print(f"Mejor en muestra:   {best.describe()}")
        print(
            f"  acierto           {best.in_sample.win_rate_pct:.1f}% dentro, "
            f"{best.out_sample.win_rate_pct:.1f}% fuera"
            if best.out_sample else ""
        )
        print(
            f"  suerte pura       {outcome.chance_hit_rate * 100:.1f}% "
            f"(lo mejor de {outcome.combinations_tested} lanzamientos de moneda)"
        )
    print(f"\nVeredicto: {outcome.verdict()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
