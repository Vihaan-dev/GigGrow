"""Debt-spiral detection and NGO escalation.

Triggers when a user shows multiple signs of financial distress at once.
The output is informational — we surface helplines, never auto-contact.
"""

NGO_HELPLINES = [
    {
        "name": "iCall (TISS)",
        "type": "psychosocial counselling",
        "phone": "+91 9152987821",
        "hours": "Mon-Sat 8:00am-10:00pm IST",
        "url": "https://icallhelpline.org",
        "languages": ["english", "hindi", "marathi", "kannada"],
    },
    {
        "name": "Snehi",
        "type": "emotional support",
        "phone": "+91 9582208181",
        "hours": "10am-6pm IST",
        "url": "https://snehi.org",
        "languages": ["english", "hindi"],
    },
    {
        "name": "RBI CMS — Banking Ombudsman",
        "type": "predatory lending grievance",
        "phone": "14448",
        "hours": "Mon-Fri 9:30am-5:15pm IST",
        "url": "https://cms.rbi.org.in",
        "languages": ["english", "hindi"],
    },
    {
        "name": "MoneyLife Foundation",
        "type": "financial counselling",
        "phone": "+91 9869913444",
        "hours": "Mon-Fri 10am-6pm IST",
        "url": "https://www.moneylife.in/foundation",
        "languages": ["english", "hindi"],
    },
]


def assess_crisis(insights, safety_status, current_savings, mandatory_spend_monthly):
    """Compute a 0..3 crisis score plus reasons.

    Score >= 2 should trigger the escalation banner.
    """
    reasons = []
    score = 0

    days_safe = (safety_status or {}).get("days_safe", 0)
    if days_safe < 2:
        score += 1
        reasons.append({
            "code": "days_safe_critical",
            "detail": "Only {0:.1f} days of mandatory spend covered.".format(days_safe),
        })

    earnings = insights.get("earnings", {}) or {}
    spending = insights.get("spending", {}) or {}
    avg_daily_earnings = earnings.get("avg_daily", 0)
    avg_daily_spending = spending.get("avg_daily", 0)

    if avg_daily_earnings > 0 and avg_daily_spending > avg_daily_earnings:
        score += 1
        reasons.append({
            "code": "spending_exceeds_earnings",
            "detail": "Daily spend Rs {0} > daily earn Rs {1}.".format(
                avg_daily_spending, avg_daily_earnings
            ),
        })

    streaks = insights.get("streaks", {}) or {}
    if streaks.get("current_low", 0) >= 4:
        score += 1
        reasons.append({
            "code": "low_earning_streak",
            "detail": "{0} consecutive low-earning days.".format(streaks["current_low"]),
        })

    monthly_burn = mandatory_spend_monthly or 0
    if monthly_burn > 0 and current_savings < monthly_burn * 0.25:
        score += 1
        reasons.append({
            "code": "savings_below_quarter_month",
            "detail": "Savings below 25% of one month of mandatory spend.",
        })

    triggered = score >= 2

    return {
        "triggered": triggered,
        "score": score,
        "reasons": reasons,
        "helplines": NGO_HELPLINES if triggered else [],
        "message": (
            "We're seeing signs of financial stress. Talking to a free counsellor can help."
            if triggered
            else None
        ),
    }
