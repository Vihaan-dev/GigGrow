"""Proactive nudges grounded in user data.

Two layers:
  1. Rule-based triggers — examine insights/forecast and decide WHICH nudges
     to surface (no LLM call wasted if nothing is wrong).
  2. Language layer — Gemini phrases the chosen triggers in the user's
     language (Hindi, Kannada, English). Each nudge cites the data it came
     from, so the user sees *why* the system is nudging them.
"""

import json
import re
from .gemini_client import generate_text

LANGUAGE_LABEL = {
    "hindi": "Hindi (Devanagari script)",
    "kannada": "Kannada (Kannada script)",
    "english": "English",
}


def _category_overspend_triggers(insights, recent_days=7):
    """Spot categories where last 7d daily avg is 30%+ over the 30d baseline."""
    triggers = []
    daily = insights.get("daily", []) or []
    if len(daily) < recent_days:
        return triggers

    recent = daily[-recent_days:]
    baseline = insights.get("spending", {}).get("by_category_daily_baseline", {}) or {}

    recent_by_cat = {}
    for d in recent:
        for cat, amount in (d.get("spending_by_category") or {}).items():
            recent_by_cat[cat] = recent_by_cat.get(cat, 0) + amount

    for cat, total in recent_by_cat.items():
        if cat in {"rent", "transfer"}:  # fixed monthly expenses, skip
            continue
        recent_daily_avg = total / recent_days
        baseline_daily = baseline.get(cat, 0)
        if baseline_daily <= 0:
            continue
        overage_pct = (recent_daily_avg - baseline_daily) / baseline_daily * 100
        if overage_pct >= 25:
            triggers.append({
                "id": "overspend_" + cat,
                "kind": "overspend",
                "severity": "warning",
                "data": {
                    "category": cat,
                    "recent_daily_avg": int(round(recent_daily_avg)),
                    "baseline_daily": int(baseline_daily),
                    "overage_pct": int(round(overage_pct)),
                },
            })
    return triggers


def _earnings_dip_trigger(insights):
    trend = insights.get("earnings", {}).get("trend_7v7", 0)
    if trend <= -0.20:
        return {
            "id": "earnings_dip",
            "kind": "earnings_dip",
            "severity": "warning",
            "data": {
                "drop_pct": int(round(abs(trend) * 100)),
                "best_day": insights.get("best_day_of_week", {}).get("name"),
                "best_day_avg": insights.get("best_day_of_week", {}).get("avg"),
            },
        }
    return None


def _safety_buffer_trigger(safety_status):
    days_safe = (safety_status or {}).get("days_safe", 0)
    if days_safe < 3:
        return {
            "id": "safety_low",
            "kind": "safety_low",
            "severity": "danger",
            "data": {"days_safe": days_safe},
        }
    if days_safe < 7:
        return {
            "id": "safety_warn",
            "kind": "safety_warn",
            "severity": "warning",
            "data": {"days_safe": days_safe},
        }
    return None


def _scheme_opportunity_trigger(matched_schemes):
    if not matched_schemes:
        return None
    free_schemes = [s for s in matched_schemes if s.get("annual_cost", 0) <= 50]
    if not free_schemes:
        return None
    pick = free_schemes[0]
    return {
        "id": "scheme_" + pick["name"],
        "kind": "scheme_opportunity",
        "severity": "info",
        "data": {
            "name": pick["name"],
            "annual_amount": pick.get("annual_amount"),
            "annual_cost": pick.get("annual_cost"),
        },
    }


def _best_day_trigger(insights):
    best = insights.get("best_day_of_week") or {}
    if not best.get("avg"):
        return None
    avg = insights.get("earnings", {}).get("avg_daily", 0)
    if avg <= 0 or best["avg"] < avg * 1.15:
        return None
    return {
        "id": "best_day",
        "kind": "opportunity",
        "severity": "info",
        "data": {
            "best_day_name": best["name"],
            "best_day_avg": best["avg"],
            "overall_avg": avg,
            "uplift_pct": int(round((best["avg"] - avg) / avg * 100)),
        },
    }


def detect_triggers(insights, safety_status=None, matched_schemes=None):
    triggers = []
    safety_trigger = _safety_buffer_trigger(safety_status)
    if safety_trigger:
        triggers.append(safety_trigger)

    triggers.extend(_category_overspend_triggers(insights))

    dip = _earnings_dip_trigger(insights)
    if dip:
        triggers.append(dip)

    best_day = _best_day_trigger(insights)
    if best_day:
        triggers.append(best_day)

    scheme = _scheme_opportunity_trigger(matched_schemes)
    if scheme:
        triggers.append(scheme)

    severity_rank = {"danger": 0, "warning": 1, "info": 2}
    triggers.sort(key=lambda t: severity_rank.get(t["severity"], 3))
    return triggers[:3]


def _strip_code_fences(text):
    if not text:
        return text
    cleaned = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, flags=re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return cleaned


def _fallback_phrase(trigger, language):
    """Deterministic natural-language phrasing per trigger kind.

    Used when Gemini is unavailable or returns a non-parseable response.
    Each branch produces grounded copy in 1-2 sentences using only the
    numbers in trigger.data — same hallucination-safety contract as the
    LLM path.
    """
    kind = trigger["kind"]
    data = trigger.get("data", {}) or {}

    HINDI = (language == "hindi")
    KAN = (language == "kannada")

    if kind == "overspend":
        cat = data.get("category", "this category")
        pct = data.get("overage_pct", 0)
        recent = data.get("recent_daily_avg", 0)
        baseline = data.get("baseline_daily", 0)
        if HINDI:
            title = f"{cat.title()} खर्च ज्यादा"
            message = f"पिछले 7 दिनों में {cat} पर रोज़ ₹{recent} खर्च हुआ, जो आपके सामान्य ₹{baseline} से {pct}% ज्यादा है।"
            action = "और देखें"
        elif KAN:
            title = f"{cat.title()} ಖರ್ಚು ಹೆಚ್ಚು"
            message = f"ಕಳೆದ 7 ದಿನಗಳಲ್ಲಿ {cat} ಮೇಲೆ ದಿನಕ್ಕೆ ₹{recent} ಖರ್ಚಾಗಿದೆ — ನಿಮ್ಮ ಸಾಮಾನ್ಯ ₹{baseline}ಗಿಂತ {pct}% ಹೆಚ್ಚು."
            action = "ಹೆಚ್ಚು ನೋಡಿ"
        else:
            title = f"{cat.title()} spend is up {pct}%"
            message = f"You averaged ₹{recent}/day on {cat} this week — that's {pct}% over your usual ₹{baseline}/day. Worth a look."
            action = "See breakdown"

    elif kind == "earnings_dip":
        drop = data.get("drop_pct", 0)
        best = data.get("best_day")
        best_avg = data.get("best_day_avg", 0)
        if HINDI:
            title = "कमाई कम हो रही है"
            message = f"पिछले 7 दिन पिछले हफ्ते से {drop}% कम हैं। {best} आपका सबसे अच्छा दिन है (₹{best_avg})—उस पर ध्यान दें।"
            action = "ट्रेंड देखें"
        elif KAN:
            title = "ಆದಾಯ ಕುಸಿತ"
            message = f"ಕಳೆದ 7 ದಿನಗಳಲ್ಲಿ {drop}% ಕಡಿಮೆ. {best} ನಿಮ್ಮ ಬಲಿಷ್ಠ ದಿನ (₹{best_avg})—ಅದರ ಮೇಲೆ ಗಮನವಿಡಿ."
            action = "ನೋಡಿ"
        else:
            title = f"Earnings down {drop}% this week"
            message = f"Last 7 days are {drop}% below the prior 7. {best} remains your best day (₹{best_avg}) — try to lean into it."
            action = "See trend"

    elif kind == "safety_low":
        days = data.get("days_safe", 0)
        if HINDI:
            title = "सुरक्षा बहुत कम"
            message = f"आपके पास सिर्फ़ {days} दिन की मूलभूत खर्च की बचत है। बड़ी खरीद टालें।"
            action = "बफर बनाएँ"
        elif KAN:
            title = "ಸುರಕ್ಷತೆ ಕಡಿಮೆ"
            message = f"ಕೇವಲ {days} ದಿನಗಳ ಮೂಲಭೂತ ಖರ್ಚಿಗೆ ಸಾಕಾಗುವಷ್ಟು ಉಳಿತಾಯವಿದೆ. ದೊಡ್ಡ ಖರ್ಚು ತಪ್ಪಿಸಿ."
            action = "ಬಫರ್ ಬೆಳೆಸಿ"
        else:
            title = f"Only {days} days of safety left"
            message = f"You have ₹{days} days of mandatory spend covered. Avoid big purchases this week and lean into your strongest earning days."
            action = "Build buffer"

    elif kind == "safety_warn":
        days = data.get("days_safe", 0)
        if HINDI:
            title = "बफर पूरी तरह से नहीं"
            message = f"आपके पास {days} दिन की सुरक्षा है। 30 दिन का लक्ष्य है—थोड़ा और जोड़ें।"
            action = "लक्ष्य देखें"
        elif KAN:
            title = "ಸ್ವಲ್ಪ ಕಡಿಮೆ ಬಫರ್"
            message = f"{days} ದಿನಗಳ ಸುರಕ್ಷತೆ ಇದೆ. 30 ದಿನಗಳ ಗುರಿ ಮುಟ್ಟಲು ಸ್ವಲ್ಪ ಸೇರಿಸಿ."
            action = "ಗುರಿ ನೋಡಿ"
        else:
            title = f"Buffer is at {days} days"
            message = f"You're at {days} days of safety. The healthy target is 30 — a small weekly add gets you there steadily."
            action = "See target"

    elif kind == "scheme_opportunity":
        name = data.get("name", "a scheme")
        amt = data.get("annual_amount", 0)
        cost = data.get("annual_cost", 0)
        if HINDI:
            title = f"{name} के लिए योग्य हैं"
            message = f"₹{cost}/साल में ₹{amt} का कवर मिलता है। आप योग्य हैं।"
            action = "अप्लाई करें"
        elif KAN:
            title = f"{name} ಗೆ ಅರ್ಹ"
            message = f"ವರ್ಷಕ್ಕೆ ₹{cost} ಗೆ ₹{amt} ರಕ್ಷಣೆ. ನೀವು ಅರ್ಹರಾಗಿದ್ದೀರಿ."
            action = "ಅರ್ಜಿ"
        else:
            title = f"You qualify for {name}"
            message = f"Just ₹{cost}/year for ₹{amt:,} of coverage. You're eligible based on your income and age — worth a one-tap apply."
            action = "Apply"

    elif kind == "opportunity":
        name = data.get("best_day_name", "your best day")
        avg = data.get("best_day_avg", 0)
        uplift = data.get("uplift_pct", 0)
        if HINDI:
            title = f"{name} सबसे अच्छा दिन"
            message = f"{name} को आप औसत ₹{avg} कमाते हैं ({uplift}% औसत से ज्यादा)। उस दिन ज्यादा शिफ्ट लें।"
            action = "प्लान करें"
        elif KAN:
            title = f"{name} ಬಲಿಷ್ಠ ದಿನ"
            message = f"{name} ದಂದು ಸರಾಸರಿ ₹{avg} ಗಳಿಸುತ್ತೀರಿ ({uplift}% ಹೆಚ್ಚು). ಆ ದಿನ ಹೆಚ್ಚು ಶಿಫ್ಟ್ ತೆಗೆದುಕೊಳ್ಳಿ."
            action = "ಯೋಜಿಸಿ"
        else:
            title = f"{name} is your strongest day"
            message = f"You average ₹{avg} on {name}s — {uplift}% above your overall daily average. Stack extra shifts there."
            action = "Plan {0}".format(name)

    else:
        title = kind.replace("_", " ").title()
        message = "There's something worth looking at in your data."
        action = "Open"

    return {
        "id": trigger["id"],
        "title": title[:80],
        "message": message[:240],
        "action": action[:24],
        "severity": trigger["severity"],
        "kind": trigger["kind"],
        "data": trigger["data"],
    }


def _phrase_nudges(triggers, language):
    if not triggers:
        return []

    label = LANGUAGE_LABEL.get(language, "English")

    prompt = (
        "You are a financial copilot for an Indian gig worker. "
        "Phrase each trigger below as a SHORT proactive nudge.\n\n"
        "Output requirements:\n"
        "- Respond ONLY with a JSON array. No preamble.\n"
        "- Each item: {{\"id\": str, \"title\": str, \"message\": str, \"action\": str}}.\n"
        "- title <= 8 words. message <= 220 chars. action <= 4 words (button label).\n"
        "- Use {language}. If Hindi or Kannada, use the native script. No English mixed in.\n"
        "- Be encouraging, specific, and reference the numbers from the trigger data.\n"
        "- Do not invent numbers. Use only the values present in the trigger.\n\n"
        "Triggers:\n{triggers}\n"
    ).format(language=label, triggers=json.dumps(triggers, ensure_ascii=False, indent=2))

    raw = (generate_text(prompt) or "").strip()
    raw_lower = raw.lower()
    looks_like_error = (
        not raw
        or "api key" in raw_lower
        or "trouble thinking" in raw_lower
        or "couldn't think" in raw_lower
    )
    if looks_like_error:
        return [_fallback_phrase(t, language) for t in triggers]

    raw = _strip_code_fences(raw)
    try:
        items = json.loads(raw)
    except (ValueError, TypeError):
        return [_fallback_phrase(t, language) for t in triggers]

    by_id = {t["id"]: t for t in triggers}
    result = []
    used_ids = set()
    for item in items if isinstance(items, list) else []:
        trigger = by_id.get(item.get("id"))
        if not trigger:
            continue
        used_ids.add(trigger["id"])
        title = (item.get("title") or "").strip()
        message = (item.get("message") or "").strip()
        action = (item.get("action") or "").strip()
        # If Gemini returned an empty or obviously bogus item, fall back.
        if not title or not message:
            result.append(_fallback_phrase(trigger, language))
            continue
        result.append({
            "id": item.get("id"),
            "title": title[:80],
            "message": message[:240],
            "action": action[:24] or "Open",
            "severity": trigger["severity"],
            "kind": trigger["kind"],
            "data": trigger["data"],
        })

    # If any triggers didn't get phrased, fill in fallbacks for them
    for trigger in triggers:
        if trigger["id"] not in used_ids:
            result.append(_fallback_phrase(trigger, language))

    return result


def build_nudges(insights, safety_status=None, matched_schemes=None, language="hindi"):
    triggers = detect_triggers(insights, safety_status, matched_schemes)
    nudges = _phrase_nudges(triggers, language)
    return {
        "language": language,
        "count": len(nudges),
        "triggers": triggers,
        "nudges": nudges,
    }
