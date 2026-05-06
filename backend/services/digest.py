"""Weekly WhatsApp digest preview.

Composes a multi-section digest from the user's actual data and asks Gemini
to phrase it as a 4-bullet WhatsApp message in the user's language. The
message is intentionally short (<= 480 chars, fits in a single WhatsApp
message preview) and never invents numbers — every bullet maps to a
specific data point passed in the prompt.
"""

import json

from .gemini_client import generate_text

LANGUAGE_LABEL = {
    "hindi": "Hindi (Devanagari script)",
    "kannada": "Kannada (Kannada script)",
    "english": "English",
}


def build_digest_context(insights, safety_status, forecast_payload, user):
    earnings = insights.get("earnings", {}) or {}
    spending = insights.get("spending", {}) or {}
    daily = insights.get("daily", []) or []
    last7 = daily[-7:] if len(daily) >= 7 else daily

    week_earned = sum(d.get("earnings", 0) for d in last7)
    week_spent = sum(d.get("spending", 0) for d in last7)
    best_day = max(last7, key=lambda d: d.get("earnings", 0)) if last7 else None
    worst_day = min(last7, key=lambda d: d.get("earnings", 0)) if last7 else None

    return {
        "user_name": user.get("name", "Friend"),
        "language": user.get("language", "english"),
        "week_earned": week_earned,
        "week_spent": week_spent,
        "week_net": week_earned - week_spent,
        "best_day": {
            "date": best_day.get("date") if best_day else None,
            "amount": best_day.get("earnings", 0) if best_day else 0,
        },
        "worst_day": {
            "date": worst_day.get("date") if worst_day else None,
            "amount": worst_day.get("earnings", 0) if worst_day else 0,
        },
        "days_safe": (safety_status or {}).get("days_safe", 0),
        "trend_7v7_pct": int((earnings.get("trend_7v7", 0) or 0) * 100),
        "next_14d_predicted_net": forecast_payload.get("predicted_net", 0),
        "best_dow_name": insights.get("best_day_of_week", {}).get("name", ""),
        "best_dow_avg": insights.get("best_day_of_week", {}).get("avg", 0),
        "category_overspend_pct": _top_overspend_pct(insights),
    }


def _top_overspend_pct(insights):
    daily = insights.get("daily", []) or []
    if len(daily) < 7:
        return 0
    last7 = daily[-7:]
    baseline = insights.get("spending", {}).get("by_category_daily_baseline", {}) or {}
    recent_by_cat = {}
    for d in last7:
        for cat, amount in (d.get("spending_by_category") or {}).items():
            if cat in {"rent", "transfer"}:
                continue
            recent_by_cat[cat] = recent_by_cat.get(cat, 0) + amount
    worst = 0
    for cat, total in recent_by_cat.items():
        recent_daily = total / 7
        baseline_daily = baseline.get(cat, 0)
        if baseline_daily > 0:
            pct = int((recent_daily - baseline_daily) / baseline_daily * 100)
            if pct > worst:
                worst = pct
    return worst


def render_digest(context):
    language = context.get("language", "english")
    label = LANGUAGE_LABEL.get(language, "English")

    prompt = (
        "You are GigShield, a financial copilot for an Indian gig worker. "
        "Compose a WhatsApp weekly digest in {language}.\n\n"
        "Strict rules:\n"
        "- 4 bullet lines max, each starting with an emoji.\n"
        "- Total under 480 characters.\n"
        "- Use ONLY the numbers in the data below. Do not invent.\n"
        "- If language is Hindi or Kannada, use the native script. No English mixed in.\n"
        "- Tone: brief, encouraging, actionable.\n"
        "- Order: 1) week summary, 2) best day, 3) one warning if relevant, "
        "4) one specific action for the coming week.\n\n"
        "Data:\n{data}\n\n"
        "Output only the digest text. No preamble, no markdown."
    ).format(language=label, data=json.dumps(context, ensure_ascii=False, indent=2))

    body = generate_text(prompt) or "Digest not available right now."
    return {
        "channel": "whatsapp",
        "language": language,
        "preview": body.strip(),
        "context": context,
    }


SUBSCRIBED_PHONES = {}  # in-memory mock: {user_id: phone}


def subscribe(user_id, phone):
    SUBSCRIBED_PHONES[user_id] = phone
    return {
        "user_id": user_id,
        "phone": phone,
        "channel": "whatsapp",
        "schedule": "Every Sunday 10:00 IST",
        "status": "subscribed",
    }


def get_subscription(user_id):
    phone = SUBSCRIBED_PHONES.get(user_id)
    if not phone:
        return None
    return {
        "user_id": user_id,
        "phone": phone,
        "channel": "whatsapp",
        "schedule": "Every Sunday 10:00 IST",
        "status": "subscribed",
    }
