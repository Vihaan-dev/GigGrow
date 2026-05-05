from collections import defaultdict
from datetime import date, timedelta
import statistics

EVENT_LABELS = {
    "holiday": "holiday",
    "weather_rain": "rain",
    "low_demand": "low_demand",
    "surge_bonus": "surge",
}


def _date_range(end_date, days):
    start = end_date - timedelta(days=days - 1)
    for offset in range(days):
        current = start + timedelta(days=offset)
        yield current


def _mean(values):
    if not values:
        return 0
    return statistics.mean(values)


def classify_day(earnings_amount, avg_earnings, event_types):
    if "holiday" in event_types:
        return "holiday"
    if "weather_rain" in event_types:
        return "rain"
    if "low_demand" in event_types:
        return "low_demand"

    if avg_earnings <= 0:
        return "unknown"

    if earnings_amount >= avg_earnings * 1.2:
        return "good"
    if earnings_amount <= avg_earnings * 0.8:
        return "bad"
    return "normal"


def build_daily_summary(earnings, spending, events, days=30, end_date=None):
    end_date = end_date or date.today()

    earnings_by_date = defaultdict(int)
    spending_by_date = defaultdict(int)
    events_by_date = defaultdict(list)

    for item in earnings:
        earnings_by_date[item["date"]] += item.get("amount", 0)

    for item in spending:
        spending_by_date[item["date"]] += item.get("amount", 0)

    for item in events:
        events_by_date[item["date"]].append(item.get("type"))

    date_keys = []
    daily_earnings = []
    for current in _date_range(end_date, days):
        key = current.isoformat()
        date_keys.append(key)
        daily_earnings.append(earnings_by_date.get(key, 0))

    recent_earnings = daily_earnings[-7:] if len(daily_earnings) >= 7 else daily_earnings
    avg_recent = _mean(recent_earnings)

    summary = []
    for key, earnings_amount in zip(date_keys, daily_earnings):
        spending_amount = spending_by_date.get(key, 0)
        event_types = events_by_date.get(key, [])
        day_type = classify_day(earnings_amount, avg_recent, event_types)
        labels = sorted({EVENT_LABELS.get(event) for event in event_types if event in EVENT_LABELS})

        summary.append({
            "date": key,
            "earnings": earnings_amount,
            "spending": spending_amount,
            "day_type": day_type,
            "labels": labels,
        })

    projected_month_earnings = int(avg_recent * 30) if avg_recent else 0

    return {
        "days": summary,
        "avg_recent_earnings": int(avg_recent),
        "projected_month_earnings": projected_month_earnings,
    }
