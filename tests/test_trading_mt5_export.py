"""
Tests for the MT5 export helpers.

The terminal itself is Windows-only and cannot run here, so the CLI is a thin
shell around these pure functions — which are what actually shape the data.
"""
from datetime import datetime, timezone

import pytest

from src.trading.data import load_csv
from src.trading.mt5_export import (
    TIMEFRAMES,
    cost_hurdle,
    rates_to_rows,
    server_time_offset,
    suggest_instrument_spec,
    write_csv,
)

# MT5 returns records indexable by field name; dicts stand in faithfully.
RATES = [
    {
        "time": 1767612600,  # 2026-01-05 11:30:00 UTC
        "open": 3936.5,
        "high": 3940.0,
        "low": 3935.0,
        "close": 3939.0,
        "tick_volume": 812,
    },
    {
        "time": 1767612300,  # deliberately out of order
        "open": 3934.0,
        "high": 3937.0,
        "low": 3933.5,
        "close": 3936.5,
        "tick_volume": 640,
    },
]


class FakeSymbolInfo:
    """Attribute-style record, the other shape MT5 hands back."""

    name = "SP500m"
    point = 0.1
    trade_tick_size = 0.1
    trade_tick_value = 0.1
    volume_min = 0.1
    volume_step = 0.1
    spread = 7  # in points, i.e. 0.7 index points
    currency_profit = "USD"


def test_rates_convert_to_sorted_rows():
    rows = rates_to_rows(RATES)
    assert [row[0] for row in rows] == [
        "2026-01-05 11:25:00",
        "2026-01-05 11:30:00",
    ]
    assert rows[1][1:] == (3936.5, 3940.0, 3935.0, 3939.0, 812.0)


def test_hours_shift_moves_server_time_onto_the_exchange_clock():
    rows = rates_to_rows(RATES, hours_shift=-2.0)
    assert rows[0][0] == "2026-01-05 09:25:00"


def test_exported_csv_is_readable_by_the_backtest_loader(tmp_path):
    path = tmp_path / "sp500m_m5.csv"
    written = write_csv(rates_to_rows(RATES), path)
    assert written == 2

    bars = load_csv(path)
    assert len(bars) == 2
    assert bars[0].timestamp == datetime(2026, 1, 5, 11, 25)
    assert bars[1].close == 3939.0
    assert bars[1].volume == 812.0


def test_server_offset_is_inferred_to_the_nearest_half_hour():
    utc_now = datetime(2026, 1, 5, 12, 0)
    assert server_time_offset(datetime(2026, 1, 5, 15, 0), utc_now) == 3.0
    assert server_time_offset(datetime(2026, 1, 5, 14, 2), utc_now) == 2.0
    assert server_time_offset(datetime(2026, 1, 5, 14, 28), utc_now) == 2.5


def test_suggested_spec_turns_the_spread_into_slippage():
    text = suggest_instrument_spec(FakeSymbolInfo(), spread_points=0.7)
    assert "symbol='SP500m'" in text
    assert "tick_size=0.1" in text
    assert "point_value=1" in text  # 0.1 tick value / 0.1 tick size
    assert "slippage_ticks=7" in text  # 0.7 points of spread = 7 ticks


def test_suggested_spec_falls_back_to_the_reported_spread():
    text = suggest_instrument_spec(FakeSymbolInfo())
    assert "slippage_ticks=7" in text


def test_cost_hurdle_prices_the_spread_into_the_required_hit_rate():
    # 0.7 points paid twice against an 8-point stop = 0.175R of cost.
    assert cost_hurdle(0.7, 8.0) == pytest.approx(0.5875)
    # A tighter stop makes the same spread far more expensive.
    assert cost_hurdle(0.7, 4.0) == pytest.approx(0.675)
    with pytest.raises(ValueError):
        cost_hurdle(0.7, 0.0)


def test_timeframe_constants_match_the_mt5_api():
    assert TIMEFRAMES["M5"] == 5
    assert TIMEFRAMES["H1"] == 16385
