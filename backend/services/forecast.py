"""Forward-looking forecast for a gig worker.

Given history (insights from profile_insights) and optional planned events,
forecasts day-by-day:
  - earnings (using day-of-week mean × event multiplier)
  - spending (using category daily baseline + scheduled monthly hits)
  - net = earnings - spending
  - cumulative savings runway

Three scenarios:
  - baseline      : DOW mean
  - optimistic    : DOW mean + 1 sigma (and surge multiplier where available)
  - pessimistic   : DOW mean - 1 sigma (and rain/holiday penalty where applicable)

Forecast is intentionally explainable — each day carries a `reason` field
listing the multipliers applied. The intelligence is visible to the user.
"""

from datetime import date, datetime, timedelta


EVENT_MULTIPLIERS = {
    "weather_rain": 0.65,
    "holiday": 0.55,
    "low_demand": 0.75,
    "surge_bonus": 1.40,
}

SCENARIO_SHIFT = {
    "baseline": 0.0,
    "optimistic": 1.0,
    "pessimistic": -1.0,
}


def _parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _planned_events_by_date(planned_events):
    by_date = {}
    if not planned_events:
        return by_date
    for evt in planned_events:
        if "date" not in evt or "type" not in evt:
            continue
        by_date.setdefault(evt["date"], []).append(evt["type"])
    return by_date


def _scheduled_monthly_spending(insights, spending_history):
    """Detect rent-day and home-transfer-day from history.

    Returns: {day_of_month: {"category": amount, ...}, ...}
    """
    schedule = {}
    if not spending_history:
        return schedule

    fixed_categories = {"rent", "transfer"}
    for item in spending_history:
        cat = item.get("category")
        if cat not in fixed_categories:
            continue
        try:
            dom = _parse_date(item["date"]).day
        except Exception:
            continue
        amount = item.get("amount", 0) or 0
        if amount <= 0:
            continue
        # keep the largest seen amount for each (dom, category) pair
        bucket = schedule.setdefault(dom, {})
        if amount > bucket.get(cat, 0):
            bucket[cat] = amount

    return schedule


def _project_earnings_for_day(target_date, insights, scenario, planned_event_types):
    dow = target_date.weekday()
    dow_pattern = insights.get("dow_pattern", {})
    base = dow_pattern.get(dow, {}).get("avg", 0)
    if base == 0:
        base = insights.get("earnings", {}).get("avg_daily", 0)

    sigma = insights.get("earnings", {}).get("std_dev", 0)
    shift = SCENARIO_SHIFT.get(scenario, 0.0)

    expected = base + shift * sigma

    multiplier = 1.0
    reasons = []
    for evt_type in planned_event_types or []:
        m = EVENT_MULTIPLIERS.get(evt_type)
        if m is None:
            continue
        multiplier *= m
        reasons.append("{0}×{1:.2f}".format(evt_type, m))

    expected = max(0, int(round(expected * multiplier)))

    low_band = max(0, int(round((base - sigma) * multiplier)))
    high_band = max(0, int(round((base + sigma) * multiplier)))

    return expected, low_band, high_band, reasons


def _project_spending_for_day(target_date, insights, monthly_schedule):
    daily_baseline = insights.get("spending", {}).get("by_category_daily_baseline", {}) or {}
    fixed_categories = {"rent", "transfer"}

    breakdown = {}
    total = 0
    for cat, amount in daily_baseline.items():
        if cat in fixed_categories:
            continue
        if amount <= 0:
            continue
        breakdown[cat] = amount
        total += amount

    monthly_hits = monthly_schedule.get(target_date.day, {})
    for cat, amount in monthly_hits.items():
        breakdown[cat] = amount
        total += amount

    return total, breakdown


def forecast_days(
    insights,
    spending_history,
    *,
    days_ahead=14,
    scenario="baseline",
    starting_savings=0,
    start_date=None,
    planned_events=None,
):
    """Return per-day forecast plus aggregates.

    The forecast is deterministic given the same insights + planned_events.
    """
    if scenario not in SCENARIO_SHIFT:
        scenario = "baseline"

    start_date = _parse_date(start_date) if start_date else date.today()
    planned_by_date = _planned_events_by_date(planned_events)
    monthly_schedule = _scheduled_monthly_spending(insights, spending_history or [])

    days = []
    cumulative_savings = starting_savings
    total_earnings = 0
    total_spending = 0

    for offset in range(days_ahead):
        target = start_date + timedelta(days=offset)
        target_iso = target.isoformat()

        planned_types = planned_by_date.get(target_iso, [])
        earnings, low_e, high_e, reasons = _project_earnings_for_day(
            target, insights, scenario, planned_types
        )
        spending, spend_breakdown = _project_spending_for_day(
            target, insights, monthly_schedule
        )

        net = earnings - spending
        cumulative_savings += net

        total_earnings += earnings
        total_spending += spending

        days.append({
            "date": target_iso,
            "dow": target.weekday(),
            "predicted_earnings": earnings,
            "predicted_spending": spending,
            "net": net,
            "savings_after": cumulative_savings,
            "earnings_low_band": low_e,
            "earnings_high_band": high_e,
            "spending_breakdown": spend_breakdown,
            "planned_events": planned_types,
            "earnings_reasons": reasons,
        })

    daily_mandatory = insights.get("spending", {}).get("avg_daily", 0) or 1
    days_to_30d_buffer = None
    target_buffer = daily_mandatory * 30
    if cumulative_savings >= target_buffer:
        days_to_30d_buffer = 0
    else:
        # If average net is positive, project days to reach 30-day buffer
        avg_net = (total_earnings - total_spending) / max(days_ahead, 1)
        if avg_net > 0:
            shortfall = target_buffer - cumulative_savings
            days_to_30d_buffer = int(shortfall // avg_net) + days_ahead

    return {
        "scenario": scenario,
        "start_date": start_date.isoformat(),
        "days_ahead": days_ahead,
        "starting_savings": starting_savings,
        "ending_savings": cumulative_savings,
        "total_predicted_earnings": total_earnings,
        "total_predicted_spending": total_spending,
        "predicted_net": total_earnings - total_spending,
        "days_to_30d_buffer": days_to_30d_buffer,
        "target_buffer": int(target_buffer),
        "daily_mandatory_estimate": int(daily_mandatory),
        "days": days,
    }


def forecast_with_purchase(
    insights,
    spending_history,
    *,
    purchase_amount,
    starting_savings,
    days_ahead=30,
    scenario="baseline",
    start_date=None,
):
    """Same as forecast_days but applies the purchase as a one-time hit on day 0.

    Useful for the purchase simulator: shows the cash-runway curve with vs without.
    """
    base = forecast_days(
        insights,
        spending_history,
        days_ahead=days_ahead,
        scenario=scenario,
        starting_savings=starting_savings,
        start_date=start_date,
    )
    after = forecast_days(
        insights,
        spending_history,
        days_ahead=days_ahead,
        scenario=scenario,
        starting_savings=starting_savings - purchase_amount,
        start_date=start_date,
    )
    return {
        "purchase_amount": purchase_amount,
        "without_purchase": base,
        "with_purchase": after,
    }
