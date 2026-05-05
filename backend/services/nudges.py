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

    raw = generate_text(prompt) or ""
    raw = _strip_code_fences(raw)

    try:
        items = json.loads(raw)
    except (ValueError, TypeError):
        return [
            {
                "id": t["id"],
                "title": t["kind"].replace("_", " ").title(),
                "message": json.dumps(t["data"], ensure_ascii=False),
                "action": "Open",
                "severity": t["severity"],
                "kind": t["kind"],
                "data": t["data"],
            }
            for t in triggers
        ]

    by_id = {t["id"]: t for t in triggers}
    result = []
    for item in items if isinstance(items, list) else []:
        trigger = by_id.get(item.get("id"))
        if not trigger:
            continue
        result.append({
            "id": item.get("id"),
            "title": item.get("title", "")[:80],
            "message": item.get("message", "")[:240],
            "action": item.get("action", "")[:24],
            "severity": trigger["severity"],
            "kind": trigger["kind"],
            "data": trigger["data"],
        })
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
