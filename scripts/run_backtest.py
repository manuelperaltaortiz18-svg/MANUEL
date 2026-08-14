#!/usr/bin/env python3
"""
Command-line backtest runner for the intraday 1:1 breakout bot.

Examples:
    # Synthetic data, defaults (MES, 5m, opening-range breakout, 1:1)
    python scripts/run_backtest.py

    # Real data, 15-minute Donchian breakout on the CFD, verbose
    python scripts/run_backtest.py --csv data/es_1m.csv --timeframe 15 \
        --instrument US500 --mode donchian --verbose
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.trading_config import (  # noqa: E402
    INSTRUMENTS,
    BotConfig,
    BreakoutConfig,
    FirstCandleBreakConfig,
    RiskConfig,
    SessionConfig,
)
from src.trading.backtest import run_backtest  # noqa: E402
from src.trading.strategy import BreakoutStrategy, FirstCandleBreakStrategy  # noqa: E402
from src.trading.data import (  # noqa: E402
    filter_session,
    load_csv,
    resample,
    synthetic_bars,
)
from src.trading.metrics import hit_rate_confidence_interval, optimal_f_note  # noqa: E402


def parse_time(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backtest the 1:1 S&P 500 breakout bot")
    p.add_argument("--csv", help="OHLCV CSV file; omit to use synthetic data")
    p.add_argument("--timeframe", type=int, default=15, help="Bar size in minutes")
    p.add_argument(
        "--instrument", default="MES", choices=sorted(INSTRUMENTS), help="Contract spec"
    )
    p.add_argument("--equity", type=float, default=25_000.0, help="Starting equity")
    p.add_argument(
        "--mode",
        default="opening_range",
        choices=("opening_range", "donchian", "first-candle"),
        help="first-candle = cierre fuera del rango de la primera vela",
    )
    p.add_argument(
        "--require-excursion",
        action="store_true",
        help="first-candle: exigir que salga del rango y vuelva antes de entrar",
    )
    p.add_argument("--range-bars", type=int, default=1, help="velas que forman el rango")
    p.add_argument("--stop-buffer-ticks", type=float, default=2.0)
    p.add_argument("--max-range-points", type=float, default=0.0)
    p.add_argument("--lookback", type=int, default=12, help="Donchian lookback in bars")
    p.add_argument("--or-minutes", type=int, default=30, help="Opening range length")
    p.add_argument("--atr-period", type=int, default=14)
    p.add_argument("--atr-multiple", type=float, default=1.0, help="Stop = mult * ATR")
    p.add_argument(
        "--reward-risk",
        type=float,
        default=1.0,
        help="Target/stop ratio; 1.0 is the 1:1 strategy",
    )
    p.add_argument("--risk-pct", type=float, default=0.5, help="%% of equity per trade")
    p.add_argument("--max-trades", type=int, default=3, help="Max entries per session")
    p.add_argument("--daily-loss-pct", type=float, default=2.0)
    p.add_argument("--longs-only", action="store_true")
    p.add_argument("--shorts-only", action="store_true")
    p.add_argument("--session-start", type=parse_time, default=time(9, 30))
    p.add_argument("--session-end", type=parse_time, default=time(16, 0))
    p.add_argument("--entry-cutoff", type=parse_time, default=time(15, 30))
    p.add_argument("--flat-at", type=parse_time, default=time(15, 45))
    p.add_argument("--days", type=int, default=120, help="Synthetic sessions to generate")
    p.add_argument("--seed", type=int, default=42, help="Synthetic data seed")
    p.add_argument("--verbose", action="store_true", help="Print every order and fill")
    p.add_argument("--list-trades", action="store_true", help="Print the trade blotter")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    session = SessionConfig(
        session_start=args.session_start,
        session_end=args.session_end,
        entry_cutoff=args.entry_cutoff,
        flat_at=args.flat_at,
        opening_range_minutes=args.or_minutes,
    )
    instrument = INSTRUMENTS[args.instrument]
    is_reclaim = args.mode == "first-candle"
    strategy_config = (
        FirstCandleBreakConfig(
            range_bars=args.range_bars,
            require_excursion=args.require_excursion,
            reward_risk_ratio=args.reward_risk,
            stop_buffer_ticks=args.stop_buffer_ticks,
            max_range_points=args.max_range_points,
            max_signals_per_day=args.max_trades,
            allow_long=not args.shorts_only,
            allow_short=not args.longs_only,
        )
        if is_reclaim
        else BreakoutConfig(
            mode=args.mode,
            lookback_bars=args.lookback,
            atr_period=args.atr_period,
            atr_multiple=args.atr_multiple,
            reward_risk_ratio=args.reward_risk,
            allow_long=not args.shorts_only,
            allow_short=not args.longs_only,
            max_signals_per_day=args.max_trades,
        )
    )
    config = BotConfig(
        instrument=instrument,
        session=session,
        risk=RiskConfig(
            risk_per_trade_pct=args.risk_pct,
            max_trades_per_day=args.max_trades,
            daily_loss_limit_pct=args.daily_loss_pct,
        ),
        strategy=strategy_config,
        starting_equity=args.equity,
        timeframe_minutes=args.timeframe,
    )

    if args.csv:
        bars = load_csv(args.csv)
        source = f"{args.csv} ({len(bars)} raw bars)"
    else:
        bars = synthetic_bars(
            days=args.days,
            minutes=args.timeframe,
            session_start=args.session_start,
            session_end=args.session_end,
            seed=args.seed,
            tick_size=instrument.tick_size,
        )
        source = f"synthetic ({args.days} sessions, seed {args.seed})"

    if args.csv and args.timeframe > 1:
        bars = resample(bars, args.timeframe)
    bars = filter_session(bars, session.session_start, session.session_end)
    if not bars:
        print("No bars inside the configured session window.", file=sys.stderr)
        return 1

    strategy = (
        FirstCandleBreakStrategy(config.strategy, instrument, session)
        if is_reclaim
        else BreakoutStrategy(config.strategy, instrument, session)
    )
    result = run_backtest(
        bars, config, logger=print if args.verbose else None, strategy=strategy
    )
    report = result.report

    print()
    print("=" * 68)
    print(f"1:1 BREAKOUT BACKTEST — {instrument.symbol} {args.timeframe}m ({args.mode})")
    print("=" * 68)
    print(f"Data                {source}")
    print(f"Bars in session     {len(bars)}  {bars[0].timestamp} -> {bars[-1].timestamp}")
    print(f"Risk per trade      {args.risk_pct:.2f}% of equity")
    print("-" * 68)
    print(report.summary())

    low, high = hit_rate_confidence_interval(report.wins, report.trades)
    print(f"Hit rate 95% CI     {low * 100:.1f}% – {high * 100:.1f}%")
    note = optimal_f_note(report)
    if note:
        print(f"\n[warning] {note}")
    if result.rejected_signals:
        print(f"\nSignals skipped     {len(result.rejected_signals)} (risk gates / sizing)")

    if args.list_trades and result.trades:
        print("\n" + "-" * 68)
        print(f"{'entry':<17}{'side':<7}{'qty':>6}{'in':>10}{'out':>10}"
              f"{'reason':>14}{'net':>11}{'R':>7}")
        for t in result.trades:
            print(
                f"{t.entry_time:%Y-%m-%d %H:%M}  {t.side.value:<7}{t.qty:>6g}"
                f"{t.entry_price:>10.2f}{t.exit_price:>10.2f}"
                f"{t.exit_reason.value:>14}{t.net_pnl:>11.2f}{t.r_multiple:>7.2f}"
            )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
