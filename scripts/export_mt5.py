#!/usr/bin/env python3
"""
Export bars from a running MetaTrader 5 terminal into a CSV the backtester reads.

Run this on the Windows machine where MT5 is installed (the terminal must be
open and logged in):

    pip install MetaTrader5
    python scripts/export_mt5.py --symbol SP500m --timeframe M5 --days 180

It writes `data/<symbol>_<timeframe>.csv` and prints a ready-to-paste
`InstrumentSpec` built from the symbol's real contract details and live spread.

Timezone: MT5 timestamps are in the broker's server time, not exchange time.
The script prints the inferred server offset. Either shift the data with
`--shift-hours`, or leave it alone and express the session hours in server time
when you run the backtest — but do one of the two, because the opening range
and the flat-at cutoff are read off these timestamps.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.trading.mt5_export import (  # noqa: E402
    TIMEFRAMES,
    cost_hurdle,
    rates_to_rows,
    server_time_offset,
    suggest_instrument_spec,
    write_csv,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export MT5 bars to CSV")
    p.add_argument("--symbol", default="SP500m", help="Exactly as shown in Market Watch")
    p.add_argument("--timeframe", default="M5", choices=sorted(TIMEFRAMES))
    p.add_argument("--days", type=int, default=180, help="How far back to export")
    p.add_argument("--out", help="Output path (default data/<symbol>_<tf>.csv)")
    p.add_argument(
        "--shift-hours",
        type=float,
        default=0.0,
        help="Hours added to every timestamp, to move server time to exchange time",
    )
    p.add_argument("--login", type=int, help="Optional: account number")
    p.add_argument("--password", help="Optional: account password")
    p.add_argument("--server", help="Optional: broker server name")
    p.add_argument("--terminal", help="Optional: path to terminal64.exe")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import MetaTrader5 as mt5
    except ImportError:
        print(
            "The MetaTrader5 package is missing. On the machine running MT5:\n"
            "    pip install MetaTrader5\n"
            "It is Windows-only — the terminal has no Linux or macOS build.",
            file=sys.stderr,
        )
        return 1

    init_kwargs = {}
    if args.terminal:
        init_kwargs["path"] = args.terminal
    if args.login and args.password and args.server:
        init_kwargs.update(
            login=args.login, password=args.password, server=args.server
        )

    if not mt5.initialize(**init_kwargs):
        print(f"Could not connect to the terminal: {mt5.last_error()}", file=sys.stderr)
        print("Is MT5 open and logged in?", file=sys.stderr)
        return 1

    try:
        info = mt5.symbol_info(args.symbol)
        if info is None:
            available = [s.name for s in (mt5.symbols_get() or [])][:40]
            print(f"Unknown symbol {args.symbol!r}.", file=sys.stderr)
            print(f"Some available symbols: {', '.join(available)}", file=sys.stderr)
            return 1
        if not info.visible:
            mt5.symbol_select(args.symbol, True)
            info = mt5.symbol_info(args.symbol)

        tick = mt5.symbol_info_tick(args.symbol)
        spread_points = None
        if tick and tick.ask and tick.bid:
            spread_points = tick.ask - tick.bid
            offset = server_time_offset(
                datetime.fromtimestamp(tick.time, tz=timezone.utc).replace(tzinfo=None),
                datetime.now(timezone.utc).replace(tzinfo=None),
            )
            print(f"Broker server time is UTC{offset:+g} (inferred from the last tick).")
            print(
                "The US cash session (09:30-16:00 New York) is therefore "
                f"{_shifted('09:30', offset + 5)}-{_shifted('16:00', offset + 5)} "
                "in server time during EST, one hour earlier during EDT."
            )

        end = datetime.now()
        start = end - timedelta(days=args.days)
        rates = mt5.copy_rates_range(
            args.symbol, TIMEFRAMES[args.timeframe], start, end
        )
        if rates is None or len(rates) == 0:
            print(
                f"No bars returned: {mt5.last_error()}\n"
                "Open a chart for this symbol and scroll back to make the terminal "
                "download history, then retry.",
                file=sys.stderr,
            )
            return 1

        rows = rates_to_rows(rates, hours_shift=args.shift_hours)
        out = Path(args.out or f"data/{args.symbol}_{args.timeframe}.csv")
        count = write_csv(rows, out)

        print(f"\nWrote {count} bars to {out}")
        print(f"Range: {rows[0][0]} -> {rows[-1][0]}")
        if args.shift_hours:
            print(f"Timestamps shifted by {args.shift_hours:+g} hours.")
        else:
            print("Timestamps are in BROKER SERVER TIME (not shifted).")

        print("\nPaste this into src/config/trading_config.py:\n")
        print(suggest_instrument_spec(info, spread_points))

        if spread_points:
            for stop in (4.0, 8.0, 15.0):
                need = cost_hurdle(spread_points, stop) * 100
                print(
                    f"\nWith a {stop:g}-point stop, the {spread_points:g}-point spread "
                    f"alone requires a {need:.1f}% hit rate to break even."
                )
    finally:
        mt5.shutdown()
    return 0


def _shifted(hhmm: str, hours: float) -> str:
    base = datetime.strptime(hhmm, "%H:%M") + timedelta(hours=hours)
    return base.strftime("%H:%M")


if __name__ == "__main__":
    raise SystemExit(main())
