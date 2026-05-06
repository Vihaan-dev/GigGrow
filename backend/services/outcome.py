"""90-day outcome projection: Current path vs GigShield path.

This is the *quantified impact* number we surface to the user (and judges):
"If Ramesh keeps doing what he's doing for 90 days vs follows the GigShield
plan: savings +Rs X, days-safe +Y, moneylender interest avoided Rs Z."

The math is intentionally transparent:

  Current path
    - Income  = forecast at baseline scenario for N days
    - Spending = forecast baseline (no behaviour change)
    - Interest = moneylender_debt * (apy / 12) * months  (simple monthly accrual)
    - Ending savings = starting + net - interest

  GigShield path
    - Income  = forecast at baseline scenario shifted by +best_day uplift action
                (capture an extra ~10% of weekly variance by leaning into best DOW)
    - Spending = forecast baseline minus 50% of the worst overspend category overage
                (cap discretionary fuel/food back to baseline)
    - Interest = moneylender refinanced to the cheapest eligible loan APY
                (or kept as-is if no eligible refinance)
    - Plus PMSBY/PMJJBY enrolment cost subtracted (peace of mind, ~Rs 38/mo)

The "actions_taken" list explains which levers were pulled so the impact
number isn't a black box.
"""

from .forecast import forecast_days


def _detect_overspend_category(insights):
    """Find the category most over its baseline in the last 7 days. Return
    (category, recent_daily_avg, baseline_daily, overage_amount) or None."""
    daily = insights.get("daily", []) or []
    if len(daily) < 7:
        return None

    recent = daily[-7:]
    baseline = insights.get("spending", {}).get("by_category_daily_baseline", {}) or {}

    recent_by_cat = {}
    for d in recent:
        for cat, amount in (d.get("spending_by_category") or {}).items():
            if cat in {"rent", "transfer"}:
                continue
            recent_by_cat[cat] = recent_by_cat.get(cat, 0) + amount

    worst = None
    worst_overage = 0
    for cat, total in recent_by_cat.items():
        recent_daily = total / 7
        baseline_daily = baseline.get(cat, 0)
        if baseline_daily <= 0:
            continue
        overage = recent_daily - baseline_daily
        if overage > worst_overage:
            worst_overage = overage
            worst = (cat, int(recent_daily), int(baseline_daily), int(overage))
    return worst


def _interest_over_months(principal, apy_pct, months):
    """Simple monthly interest accrual on outstanding principal (no amortisation).
    For the demo we model the moneylender as interest-only — a realistic
    pessimistic baseline since most informal loans roll over."""
    if principal <= 0 or apy_pct <= 0:
        return 0
    monthly_rate = apy_pct / 100 / 12
    return int(round(principal * monthly_rate * months))


def project_outcome(
    insights,
    spending_history,
    user,
    matched_loans,
    matched_schemes,
    *,
    horizon_days=90,
):
    starting_savings = user.get("current_savings", 0) or 0
    moneylender_debt = user.get("moneylender_debt", 0) or 0
    moneylender_apy = user.get("moneylender_apy", 0) or 0

    months = horizon_days / 30.0

    # Current path: pure baseline forecast, no behaviour change
    current = forecast_days(
        insights,
        spending_history,
        days_ahead=horizon_days,
        scenario="baseline",
        starting_savings=starting_savings,
    )
    current_interest = _interest_over_months(moneylender_debt, moneylender_apy, months)
    current_ending = current["ending_savings"] - current_interest

    # Use the user's declared mandatory spend as the floor for "days safe"
    # so this metric stays consistent with /api/safety. Observed spending
    # often understates true outflow because rent/home-transfer are paid
    # in cash and don't appear in SMS history.
    declared_mandatory_daily = (user.get("mandatory_spend", 0) or 0) / 7
    daily_mandatory = declared_mandatory_daily if declared_mandatory_daily > 0 else (
        current.get("daily_mandatory_estimate", 0) or 1
    )
    current_days_safe_end = current_ending / daily_mandatory

    # GigShield path: lean into best DOW + cap worst overspend + refinance
    # We model the interventions as net lifts, not by re-running the forecast
    # day-by-day with a different model.
    overspend = _detect_overspend_category(insights)
    cap_savings_per_day = (overspend[3] // 2) if overspend else 0  # cap half the overage
    cap_savings_total = cap_savings_per_day * horizon_days

    best_dow = insights.get("best_day_of_week") or {}
    best_avg = best_dow.get("avg") or 0
    overall_avg = insights.get("earnings", {}).get("avg_daily") or 0
    weekend_uplift_per_week = max(0, int((best_avg - overall_avg) * 0.25))
    uplift_total = weekend_uplift_per_week * (horizon_days // 7)

    # Refinance to cheapest eligible loan if it beats the moneylender
    refinance_apy = moneylender_apy
    refinance_partner = None
    if matched_loans:
        cheapest = min(matched_loans, key=lambda l: l.get("apy", 9999))
        if cheapest.get("apy", 9999) < moneylender_apy:
            refinance_apy = cheapest["apy"]
            refinance_partner = cheapest["name"]
    gigshield_interest = _interest_over_months(moneylender_debt, refinance_apy, months)

    # Free / cheap scheme enrolment cost (PMSBY ~Rs 20/yr + PMJJBY ~Rs 436/yr)
    cheap_schemes = [s for s in (matched_schemes or []) if s.get("annual_cost", 0) <= 500]
    scheme_annual_cost = sum(s.get("annual_cost", 0) for s in cheap_schemes[:2])
    scheme_horizon_cost = int(scheme_annual_cost * (horizon_days / 365.0))
    scheme_coverage_total = sum(s.get("annual_amount", 0) for s in cheap_schemes[:2])

    gigshield_ending = (
        current["ending_savings"]
        + cap_savings_total
        + uplift_total
        - gigshield_interest
        - scheme_horizon_cost
    )
    gigshield_days_safe_end = gigshield_ending / daily_mandatory

    actions = []
    if overspend and cap_savings_total > 0:
        actions.append({
            "code": "cap_overspend",
            "title": "Cap {0} spend back to baseline".format(overspend[0]),
            "detail": "Saves ~Rs {0}/day = Rs {1} over {2} days.".format(
                cap_savings_per_day, cap_savings_total, horizon_days
            ),
            "delta": cap_savings_total,
        })
    if uplift_total > 0:
        actions.append({
            "code": "best_day_uplift",
            "title": "Lean into {0} surge zones".format(best_dow.get("name") or "best day"),
            "detail": "Capture 25% of weekly best-day uplift (~Rs {0}/week) = Rs {1}.".format(
                weekend_uplift_per_week, uplift_total
            ),
            "delta": uplift_total,
        })
    if refinance_partner and (current_interest - gigshield_interest) > 0:
        actions.append({
            "code": "refinance",
            "title": "Refinance moneylender to {0}".format(refinance_partner),
            "detail": "Drops APY {0}% → {1}%. Saves Rs {2} interest over {3} days.".format(
                moneylender_apy, refinance_apy,
                current_interest - gigshield_interest, horizon_days
            ),
            "delta": current_interest - gigshield_interest,
        })
    if cheap_schemes:
        names = ", ".join(s["name"] for s in cheap_schemes[:2])
        actions.append({
            "code": "scheme_enrol",
            "title": "Enrol in {0}".format(names),
            "detail": "Costs Rs {0} for {1} days, covers Rs {2} downside risk.".format(
                scheme_horizon_cost, horizon_days, scheme_coverage_total
            ),
            "delta": -scheme_horizon_cost,
        })

    delta_savings = gigshield_ending - current_ending
    delta_interest = current_interest - gigshield_interest
    delta_days_safe = gigshield_days_safe_end - current_days_safe_end

    return {
        "horizon_days": horizon_days,
        "starting_savings": starting_savings,
        "moneylender_debt": moneylender_debt,
        "moneylender_apy": moneylender_apy,
        "current_path": {
            "ending_savings": int(current_ending),
            "days_safe_end": round(current_days_safe_end, 1),
            "interest_paid": current_interest,
            "label": "Current trajectory",
        },
        "gigshield_path": {
            "ending_savings": int(gigshield_ending),
            "days_safe_end": round(gigshield_days_safe_end, 1),
            "interest_paid": gigshield_interest,
            "scheme_coverage_added": scheme_coverage_total,
            "label": "GigShield plan",
        },
        "delta": {
            "savings": int(delta_savings),
            "days_safe": round(delta_days_safe, 1),
            "interest_avoided": int(delta_interest),
        },
        "actions": actions,
    }
