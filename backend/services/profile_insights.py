"""Profile insights for a gig worker.

Builds a per-user behavioural profile from raw earnings/spending/events:
  - day-of-week earning patterns
  - category spending baselines + mix
  - income volatility (std dev, coefficient of variation)
  - streaks (consecutive low / high days)
  - 30-day trend direction

These insights are the input for forecasting and nudge generation.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
import statistics

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _aggregate_by_date(items, value_key="amount"):
    by_date = defaultdict(int)
    for item in items:
        by_date[item["date"]] += item.get(value_key, 0) or 0
    return by_date


def _aggregate_spending_by_category(spending):
    by_category = defaultdict(int)
    daily_by_category = defaultdict(lambda: defaultdict(int))
    for item in spending:
        cat = item.get("category", "other") or "other"
        amount = item.get("amount", 0) or 0
        by_category[cat] += amount
        daily_by_category[item["date"]][cat] += amount
    return dict(by_category), {d: dict(c) for d, c in daily_by_category.items()}


def _dow_earnings(earnings_by_date, all_dates):
    by_dow = defaultdict(list)
    for d in all_dates:
        dow = _parse_date(d).weekday()
        by_dow[dow].append(earnings_by_date.get(d, 0))

    pattern = {}
    for dow in range(7):
        values = by_dow.get(dow, [])
        if values:
            pattern[dow] = {
                "name": DAY_NAMES[dow],
                "avg": int(round(statistics.mean(values))),
                "median": int(statistics.median(values)),
                "samples": len(values),
            }
        else:
            pattern[dow] = {"name": DAY_NAMES[dow], "avg": 0, "median": 0, "samples": 0}
    return pattern


def _streaks(daily_earnings_values, avg):
    """Longest consecutive runs above/below the daily average."""
    if not daily_earnings_values or avg <= 0:
        return {"longest_low": 0, "longest_high": 0, "current_low": 0, "current_high": 0}

    low_threshold = avg * 0.7
    high_threshold = avg * 1.2

    longest_low = current_low = 0
    longest_high = current_high = 0
    for v in daily_earnings_values:
        if v <= low_threshold:
            current_low += 1
            current_high = 0
        elif v >= high_threshold:
            current_high += 1
            current_low = 0
        else:
            current_low = 0
            current_high = 0
        longest_low = max(longest_low, current_low)
        longest_high = max(longest_high, current_high)

    # current streak is the trailing count
    trail_low = trail_high = 0
    for v in reversed(daily_earnings_values):
        if v <= low_threshold and trail_high == 0:
            trail_low += 1
        elif v >= high_threshold and trail_low == 0:
            trail_high += 1
        else:
            break

    return {
        "longest_low": longest_low,
        "longest_high": longest_high,
        "current_low": trail_low,
        "current_high": trail_high,
    }


def _trend_direction(daily_values):
    """Compare last-7 mean to prior-7 mean. Returns -1..+1."""
    if len(daily_values) < 14:
        return 0.0
    recent = statistics.mean(daily_values[-7:])
    prior = statistics.mean(daily_values[-14:-7])
    if prior <= 0:
        return 0.0
    delta = (recent - prior) / prior
    return round(max(-1.0, min(1.0, delta)), 2)


def build_profile_insights(earnings, spending, events, days=30, end_date=None):
    """Return a dict of behavioural insights for the dashboard + forecast.

    The output shape is stable so the frontend can render against it directly.
    """
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=days - 1)

    all_dates = []
    cursor = start_date
    while cursor <= end_date:
        all_dates.append(cursor.isoformat())
        cursor += timedelta(days=1)

    earnings_by_date = _aggregate_by_date(earnings)
    spending_by_date = _aggregate_by_date(spending)
    category_totals, daily_category = _aggregate_spending_by_category(spending)

    daily_earnings_values = [earnings_by_date.get(d, 0) for d in all_dates]
    daily_spending_values = [spending_by_date.get(d, 0) for d in all_dates]

    nonzero_earnings = [v for v in daily_earnings_values if v > 0]
    earnings_avg = int(round(statistics.mean(nonzero_earnings))) if nonzero_earnings else 0
    earnings_std = int(round(statistics.stdev(nonzero_earnings))) if len(nonzero_earnings) > 1 else 0
    cv = round(earnings_std / earnings_avg, 2) if earnings_avg > 0 else 0.0

    spending_avg = int(round(statistics.mean(daily_spending_values))) if daily_spending_values else 0

    dow_pattern = _dow_earnings(earnings_by_date, all_dates)
    earning_dows = [(dow, info["avg"]) for dow, info in dow_pattern.items() if info["samples"] > 0]
    if earning_dows:
        best_dow = max(earning_dows, key=lambda x: x[1])
        worst_dow = min(earning_dows, key=lambda x: x[1])
    else:
        best_dow = (0, 0)
        worst_dow = (0, 0)

    total_spending = sum(category_totals.values()) or 1
    category_mix = {
        cat: round(amount * 100 / total_spending, 1)
        for cat, amount in category_totals.items()
    }
    category_baseline_daily = {
        cat: int(round(amount / max(days, 1)))
        for cat, amount in category_totals.items()
    }

    streaks = _streaks(daily_earnings_values, earnings_avg)
    trend = _trend_direction(daily_earnings_values)

    return {
        "window_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "earnings": {
            "avg_daily": earnings_avg,
            "std_dev": earnings_std,
            "cv": cv,
            "active_days": len(nonzero_earnings),
            "trend_7v7": trend,
        },
        "spending": {
            "avg_daily": spending_avg,
            "total": sum(daily_spending_values),
            "by_category_total": category_totals,
            "by_category_mix_pct": category_mix,
            "by_category_daily_baseline": category_baseline_daily,
        },
        "dow_pattern": dow_pattern,
        "best_day_of_week": {"dow": best_dow[0], "name": DAY_NAMES[best_dow[0]], "avg": best_dow[1]},
        "worst_day_of_week": {"dow": worst_dow[0], "name": DAY_NAMES[worst_dow[0]], "avg": worst_dow[1]},
        "streaks": streaks,
        "daily": [
            {
                "date": d,
                "dow": _parse_date(d).weekday(),
                "earnings": earnings_by_date.get(d, 0),
                "spending": spending_by_date.get(d, 0),
                "spending_by_category": daily_category.get(d, {}),
                "net": earnings_by_date.get(d, 0) - spending_by_date.get(d, 0),
            }
            for d in all_dates
        ],
    }
