import statistics


def calculate_safety_buffer(earnings_30_days, mandatory_spend_daily):
    if not earnings_30_days or len(earnings_30_days) < 3:
        return {"error": "need_at_least_3_days"}

    avg = statistics.mean(earnings_30_days)
    std_dev = statistics.stdev(earnings_30_days) if len(earnings_30_days) > 1 else 0

    worst_case = max(0, int(avg - (2 * std_dev)))
    daily_deficit = max(0, mandatory_spend_daily - worst_case)
    recommended_buffer = int(mandatory_spend_daily * 30)

    return {
        "avg_daily_earnings": int(avg),
        "std_dev": round(std_dev, 2),
        "worst_case_day": worst_case,
        "daily_deficit_worst_case": daily_deficit,
        "recommended_buffer": recommended_buffer,
    }


def check_safety_status(current_savings, daily_mandatory):
    days_safe = current_savings / daily_mandatory if daily_mandatory > 0 else 0

    if days_safe >= 30:
        status = "secure"
    elif days_safe >= 7:
        status = "okay"
    else:
        status = "at_risk"

    return {
        "days_safe": round(days_safe, 1),
        "status": status,
        "current_savings": current_savings,
    }
