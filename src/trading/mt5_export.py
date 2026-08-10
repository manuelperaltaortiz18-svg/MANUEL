"""
Helpers to turn MetaTrader 5 data into what the backtester consumes.

The MT5 terminal only runs on the user's own machine, so this module holds the
pure, testable half of the export (conversion, CSV writing, contract-spec
inference) while `scripts/export_mt5.py` is the thin CLI that talks to the
terminal.

Two MT5 facts drive everything here:

* Bar times are in the **broker's server timezone**, typically UTC+2/+3, not
  exchange time. The bot compares bar times against session hours, so either
  the times are shifted or the session hours are expressed in server time.
* An index CFD's cost is the spread, not a commission. `suggest_instrument_spec`
  reads the live spread and turns it into `slippage_ticks`, so the backtest
  charges what the broker actually charges.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

# MT5 timeframe constants, hardcoded so this module imports without the package.
TIMEFRAMES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 16385,
    "H4": 16388,
    "D1": 16408,
}

TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240}

CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")


def rates_to_rows(rates: Iterable[Any], hours_shift: float = 0.0) -> list[tuple]:
    """
    Convert MT5 rate records into CSV rows.

    Each record is a mapping or numpy void with `time` (epoch seconds, server
    timezone), `open`, `high`, `low`, `close` and `tick_volume`. `hours_shift`
    is added to every timestamp — use it to move server time onto the exchange
    clock the session hours are written in.
    """
    offset = timedelta(hours=hours_shift)
    rows = []
    for rate in rates:
        stamp = datetime.fromtimestamp(int(_field(rate, "time")), tz=timezone.utc)
        stamp = stamp.replace(tzinfo=None) + offset
        rows.append(
            (
                stamp.strftime("%Y-%m-%d %H:%M:%S"),
                float(_field(rate, "open")),
                float(_field(rate, "high")),
                float(_field(rate, "low")),
                float(_field(rate, "close")),
                float(_field(rate, "tick_volume", default=0) or 0),
            )
        )
    rows.sort(key=lambda row: row[0])
    return rows


def _field(record: Any, name: str, default: Any = None) -> Any:
    """Read a field from a dict, a numpy void, or an attribute-style object."""
    try:
        return record[name]
    except (TypeError, KeyError, IndexError, ValueError):
        value = getattr(record, name, default)
        if value is None and default is None:
            raise KeyError(f"Missing field {name!r} in MT5 record") from None
        return value


def write_csv(rows: Sequence[tuple], path: str | Path) -> int:
    """Write rows in the layout `src.trading.data.load_csv` reads. Returns count."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)
    return len(rows)


def server_time_offset(server_now: datetime, utc_now: datetime) -> float:
    """
    Infer the broker's UTC offset in hours, rounded to the nearest half hour.

    MT5 exposes no timezone field, so the offset is read from the gap between
    the last tick's timestamp and the real clock.
    """
    delta_hours = (server_now - utc_now).total_seconds() / 3600.0
    return round(delta_hours * 2) / 2


def suggest_instrument_spec(info: Any, spread_points: Optional[float] = None) -> str:
    """
    Render a ready-to-paste `InstrumentSpec` from an MT5 `symbol_info`.

    The spread becomes `slippage_ticks` because the bot pays it twice: buying at
    the ask on entry and selling at the bid on a stop exit. That is the real
    cost of a "commission-free" CFD.
    """
    name = _field(info, "name", default="CFD")
    point = float(_field(info, "point", default=0.1) or 0.1)
    tick_size = float(_field(info, "trade_tick_size", default=0) or point)
    tick_value = float(_field(info, "trade_tick_value", default=0) or 0.0)
    volume_min = float(_field(info, "volume_min", default=0.1) or 0.1)
    volume_step = float(_field(info, "volume_step", default=0.1) or 0.1)
    currency = _field(info, "currency_profit", default="USD")

    if spread_points is None:
        spread_points = float(_field(info, "spread", default=0) or 0.0) * point
    point_value = tick_value / tick_size if tick_size else 1.0
    slippage_ticks = spread_points / tick_size if tick_size else 1.0

    return (
        "InstrumentSpec(\n"
        f"    symbol={name!r},\n"
        f"    tick_size={tick_size:g},\n"
        f"    point_value={point_value:g},   # currency per 1.0 point per 1.0 lot\n"
        f"    qty_step={volume_step:g},\n"
        f"    min_qty={volume_min:g},\n"
        "    commission_per_unit=0.0,   # check your account: some CFDs do charge\n"
        f"    slippage_ticks={slippage_ticks:g},   # live spread was {spread_points:g} points\n"
        f"    currency={currency!r},\n"
        ")"
    )


def cost_hurdle(spread_points: float, stop_points: float) -> float:
    """
    Hit rate (0-1) a 1:1 strategy needs just to cover the spread.

    Paid twice — entry and exit — so a 0.7 point spread against an 8 point stop
    already demands nearly 59%.
    """
    if stop_points <= 0:
        raise ValueError("stop_points must be positive")
    cost_r = 2 * spread_points / stop_points
    return (1.0 + cost_r) / 2.0
