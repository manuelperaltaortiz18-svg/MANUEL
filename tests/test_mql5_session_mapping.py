"""
Parity check for the MQL5 session-time conversion.

`mql5/NasdaqFirstCandle.mq5` converts a New York session time into the broker's
server clock. That conversion is the one mistake in this strategy that produces
no error at all — get it wrong and the EA calmly measures "the first candle of
the open" over a different hour of the day.

MetaEditor is out of reach here, so the same arithmetic is reimplemented below
and pinned against real calendar dates. If the EA's rule changes, these
expectations are the written record of what it used to do.
"""
from datetime import date

import pytest


def day_of_week(year: int, month: int, day: int) -> int:
    """0 = Sunday, matching MqlDateTime.day_of_week."""
    return (date(year, month, day).weekday() + 1) % 7


def first_sunday(year: int, month: int) -> int:
    return 1 + ((7 - day_of_week(year, month, 1)) % 7)


def last_sunday(year: int, month: int) -> int:
    days = 31 if month in (1, 3, 5, 7, 8, 10, 12) else 30
    if month == 2:
        days = 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28
    return days - day_of_week(year, month, days)


def is_us_dst(d: date) -> bool:
    """Second Sunday in March to the first Sunday in November."""
    if d.month < 3 or d.month > 11:
        return False
    if 3 < d.month < 11:
        return True
    if d.month == 3:
        return d.day >= first_sunday(d.year, 3) + 7
    return d.day < first_sunday(d.year, 11)


def is_eu_dst(d: date) -> bool:
    """Last Sunday in March to the last Sunday in October."""
    if d.month < 3 or d.month > 10:
        return False
    if 3 < d.month < 10:
        return True
    if d.month == 3:
        return d.day >= last_sunday(d.year, 3)
    return d.day < last_sunday(d.year, 10)


def ny_to_server_minutes(d: date, broker_gmt: int, broker_dst: bool) -> int:
    server_offset = broker_gmt + (1 if (broker_dst and is_eu_dst(d)) else 0)
    ny_offset = -5 + (1 if is_us_dst(d) else 0)
    return (server_offset - ny_offset) * 60


def server_open(d: date, broker_gmt: int, broker_dst: bool, hour=9, minute=30) -> str:
    total = (hour * 60 + minute + ny_to_server_minutes(d, broker_gmt, broker_dst)) % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


# ---------------------------------------------------------------------------
#  Daylight saving boundaries
# ---------------------------------------------------------------------------


def test_us_dst_boundaries_for_2026():
    """US DST 2026: 8 March to 1 November."""
    assert not is_us_dst(date(2026, 3, 7))
    assert is_us_dst(date(2026, 3, 8))
    assert is_us_dst(date(2026, 10, 31))
    assert not is_us_dst(date(2026, 11, 1))
    assert not is_us_dst(date(2026, 1, 15))
    assert is_us_dst(date(2026, 7, 15))


def test_eu_dst_boundaries_for_2026():
    """EU DST 2026: 29 March to 25 October."""
    assert not is_eu_dst(date(2026, 3, 28))
    assert is_eu_dst(date(2026, 3, 29))
    assert is_eu_dst(date(2026, 10, 24))
    assert not is_eu_dst(date(2026, 10, 25))


def test_the_two_calendars_disagree_for_three_weeks_in_spring():
    """
    The window that breaks naive conversions: the US has already sprung
    forward while Europe has not, so the gap is one hour smaller.
    """
    mismatch = date(2026, 3, 20)
    assert is_us_dst(mismatch)
    assert not is_eu_dst(mismatch)


# ---------------------------------------------------------------------------
#  The mapping the EA prints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "day,expected",
    [
        (date(2026, 1, 15), "16:30"),   # invierno en los dos lados
        (date(2026, 7, 15), "16:30"),   # verano en los dos lados
        (date(2026, 3, 20), "15:30"),   # EEUU ya cambio, Europa no
        (date(2026, 10, 28), "15:30"),  # Europa ya volvio, EEUU no
    ],
)
def test_broker_that_follows_eu_dst(day, expected):
    """A GMT+2 broker on EU rules: 16:30 most of the year, 15:30 in the gaps."""
    assert server_open(day, broker_gmt=2, broker_dst=True) == expected


@pytest.mark.parametrize(
    "day,expected",
    [
        (date(2026, 1, 15), "16:30"),
        (date(2026, 7, 15), "15:30"),   # el broker no cambia, Nueva York si
    ],
)
def test_broker_with_a_fixed_clock(day, expected):
    assert server_open(day, broker_gmt=2, broker_dst=False) == expected


def test_a_gmt3_broker_is_one_hour_later():
    assert server_open(date(2026, 1, 15), broker_gmt=3, broker_dst=False) == "17:30"


def test_a_utc_broker_matches_the_new_york_offset():
    """With the broker on GMT, the shift is just New York's own offset."""
    assert server_open(date(2026, 1, 15), broker_gmt=0, broker_dst=False) == "14:30"
    assert server_open(date(2026, 7, 15), broker_gmt=0, broker_dst=False) == "13:30"


def test_the_conversion_never_leaves_the_clock():
    for month in range(1, 13):
        text = server_open(date(2026, month, 15), broker_gmt=3, broker_dst=True)
        hours, minutes = (int(part) for part in text.split(":"))
        assert 0 <= hours < 24 and 0 <= minutes < 60
