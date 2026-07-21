"""
§5–§8, §10, §46, §47, §61 — Return analysis: historical windows, rolling returns,
recovery times, total returns, missed best days.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class ReturnWindows:
    """§5–§6 — Multi-period return summary."""
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    return_3y: float | None = None
    return_5y: float | None = None
    return_10y: float | None = None
    return_15y: float | None = None
    return_20y: float | None = None
    cagr_3y: float | None = None
    cagr_5y: float | None = None
    cagr_10y: float | None = None
    cagr_15y: float | None = None
    cagr_20y: float | None = None


@dataclass
class RollingStats:
    """§7 — Rolling return statistics for a given window."""
    window_years: int
    median: float
    worst: float
    best: float
    pct_positive: float
    std_dev: float
    count: int


@dataclass
class DrawdownEvent:
    """§10 — A peak-to-trough-to-recovery event."""
    peak_date: str
    trough_date: str
    recovery_date: str | None
    max_drawdown_pct: float
    drawdown_days: int
    recovery_days: int | None


def cagr(begin_value: float, end_value: float, years: float) -> float:
    if begin_value <= 0 or years <= 0:
        return 0.0
    return (end_value / begin_value) ** (1 / years) - 1


def compute_return_windows(prices: list[tuple[str, float]]) -> ReturnWindows:
    """Compute return windows from a date-sorted price series (total return)."""
    if len(prices) < 2:
        return ReturnWindows()

    end_price = prices[-1][1]
    n = len(prices)

    def _find_price_months_ago(months: int) -> float | None:
        target_idx = n - 1 - months * 21  # approx trading days
        if target_idx < 0:
            return None
        return prices[target_idx][1]

    def _find_price_years_ago(years: int) -> float | None:
        target_idx = n - 1 - years * 252
        if target_idx < 0:
            return None
        return prices[target_idx][1]

    def _ret(p: float | None) -> float | None:
        return (end_price / p - 1) if p else None

    def _cagr(p: float | None, years: int) -> float | None:
        return cagr(p, end_price, years) if p else None

    p1m = _find_price_months_ago(1)
    p3m = _find_price_months_ago(3)
    p6m = _find_price_months_ago(6)
    p1y = _find_price_years_ago(1)
    p3y = _find_price_years_ago(3)
    p5y = _find_price_years_ago(5)
    p10y = _find_price_years_ago(10)
    p15y = _find_price_years_ago(15)
    p20y = _find_price_years_ago(20)

    return ReturnWindows(
        return_1m=_ret(p1m),
        return_3m=_ret(p3m),
        return_6m=_ret(p6m),
        return_1y=_ret(p1y),
        return_3y=_ret(p3y),
        return_5y=_ret(p5y),
        return_10y=_ret(p10y),
        return_15y=_ret(p15y),
        return_20y=_ret(p20y),
        cagr_3y=_cagr(p3y, 3),
        cagr_5y=_cagr(p5y, 5),
        cagr_10y=_cagr(p10y, 10),
        cagr_15y=_cagr(p15y, 15),
        cagr_20y=_cagr(p20y, 20),
    )


def compute_rolling_returns(
    prices: list[tuple[str, float]],
    window_years: int,
) -> RollingStats:
    """§7 — Compute rolling return statistics."""
    step = 252 * window_years
    if len(prices) < step + 1:
        return RollingStats(window_years, 0, 0, 0, 0, 0, 0)

    returns = []
    for i in range(len(prices) - step):
        r = cagr(prices[i][1], prices[i + step][1], window_years)
        returns.append(r)

    returns.sort()
    n = len(returns)
    median = returns[n // 2]
    worst = returns[0]
    best = returns[-1]
    pct_positive = sum(1 for r in returns if r > 0) / n
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / n
    std = math.sqrt(variance)

    return RollingStats(
        window_years=window_years,
        median=round(median, 4),
        worst=round(worst, 4),
        best=round(best, 4),
        pct_positive=round(pct_positive, 4),
        std_dev=round(std, 4),
        count=n,
    )


def compute_drawdowns(
    prices: list[tuple[str, float]],
    threshold_pct: float = -0.10,
) -> list[DrawdownEvent]:
    """§10 — Find drawdown events exceeding threshold."""
    events: list[DrawdownEvent] = []
    peak = prices[0][1]
    peak_date = prices[0][0]
    trough = peak
    trough_date = peak_date
    in_drawdown = False

    for date, price in prices[1:]:
        if price > peak:
            if in_drawdown:
                dd_pct = (trough / peak - 1)
                if dd_pct <= threshold_pct:
                    dd_days = _date_diff(peak_date, trough_date)
                    rec_days = _date_diff(trough_date, date)
                    events.append(DrawdownEvent(
                        peak_date=peak_date,
                        trough_date=trough_date,
                        recovery_date=date,
                        max_drawdown_pct=round(dd_pct, 4),
                        drawdown_days=dd_days,
                        recovery_days=rec_days,
                    ))
                in_drawdown = False
            peak = price
            peak_date = date
            trough = price
            trough_date = date
        elif price < trough:
            trough = price
            trough_date = date
            in_drawdown = True

    if in_drawdown:
        dd_pct = (trough / peak - 1)
        if dd_pct <= threshold_pct:
            dd_days = _date_diff(peak_date, trough_date)
            events.append(DrawdownEvent(
                peak_date=peak_date,
                trough_date=trough_date,
                recovery_date=None,
                max_drawdown_pct=round(dd_pct, 4),
                drawdown_days=dd_days,
                recovery_days=None,
            ))

    return events


def missed_best_days_impact(
    daily_returns: list[float],
    days_to_miss: list[int] | None = None,
) -> dict[int, float]:
    """§61 — Impact of missing the N best days."""
    if days_to_miss is None:
        days_to_miss = [5, 10, 20, 30]

    sorted_returns = sorted(daily_returns, reverse=True)
    total = 1.0
    for r in daily_returns:
        total *= (1 + r)
    full_cagr = total ** (252 / len(daily_returns)) - 1 if len(daily_returns) > 0 else 0

    results: dict[int, float] = {0: round(full_cagr, 4)}
    for n in days_to_miss:
        if n >= len(sorted_returns):
            continue
        excluded = set(range(n))
        ranked = sorted(range(len(daily_returns)), key=lambda i: daily_returns[i], reverse=True)
        exclude_indices = set(ranked[:n])
        product = 1.0
        for i, r in enumerate(daily_returns):
            if i not in exclude_indices:
                product *= (1 + r)
        adj_cagr = product ** (252 / (len(daily_returns) - n)) - 1
        results[n] = round(adj_cagr, 4)

    return results


def _date_diff(d1: str, d2: str) -> int:
    from datetime import date
    a = date.fromisoformat(d1)
    b = date.fromisoformat(d2)
    return abs((b - a).days)
