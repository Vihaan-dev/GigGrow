"""Auto-narrated dashboard briefing.

We give Gemini a structured snapshot of the user's last 30 days + their
forecast + their planned outcome, and ask it to compose a 4-5 sentence
briefing in their language.

Two protections against hallucination:
  1. The prompt explicitly forbids inventing numbers — Gemini must only
     reuse values from the snapshot dict.
  2. The output is post-validated: every Indian-rupee mention in the
     response must match a value in the snapshot, otherwise we strip
     the briefing back to a deterministic fallback.
"""

import hashlib
import json
import re

from .gemini_client import generate_text

LANGUAGE_LABEL = {
    "hindi": "Hindi (Devanagari script only — no English words)",
    "kannada": "Kannada (Kannada script only — no English words)",
    "english": "English",
}

_CACHE = {}  # {(user_id, snapshot_hash, language): briefing_text}


def _snapshot_hash(snapshot, language):
    raw = json.dumps(snapshot, sort_keys=True) + "|" + language
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def build_briefing_snapshot(insights, safety, forecast, outcome, user):
    """Compose a compact JSON dict that Gemini can safely cite."""
    earnings = insights.get("earnings", {}) or {}
    spending = insights.get("spending", {}) or {}
    daily = insights.get("daily", []) or []
    last7 = daily[-7:] if len(daily) >= 7 else daily
    week_earned = sum(d.get("earnings", 0) for d in last7)
    week_spent = sum(d.get("spending", 0) for d in last7)

    overspend = None
    baseline = spending.get("by_category_daily_baseline", {}) or {}
    recent = {}
    for d in last7:
        for cat, amt in (d.get("spending_by_category") or {}).items():
            if cat in {"rent", "transfer"}:
                continue
            recent[cat] = recent.get(cat, 0) + amt
    for cat, total in recent.items():
        if baseline.get(cat, 0) > 0:
            recent_daily = total / 7
            pct = int((recent_daily - baseline[cat]) / baseline[cat] * 100)
            if pct < 15:
                continue
            if overspend is None or pct > overspend["pct_over"]:
                overspend = {
                    "category": cat,
                    "recent_daily_avg": int(round(recent_daily)),
                    "baseline_daily": int(baseline[cat]),
                    "pct_over": pct,
                }

    return {
        "user_name": user.get("name"),
        "occupation": user.get("occupation"),
        "city": user.get("city"),
        "goal": user.get("goal"),
        "last_7_days": {
            "earned": week_earned,
            "spent": week_spent,
            "net": week_earned - week_spent,
        },
        "earnings": {
            "avg_daily": earnings.get("avg_daily"),
            "cv": earnings.get("cv"),
            "trend_7v7_pct": int((earnings.get("trend_7v7", 0) or 0) * 100),
        },
        "best_day_of_week": insights.get("best_day_of_week", {}).get("name"),
        "best_day_avg": insights.get("best_day_of_week", {}).get("avg"),
        "worst_day_of_week": insights.get("worst_day_of_week", {}).get("name"),
        "safety": {
            "days_safe": (safety or {}).get("days_safe"),
            "status": (safety or {}).get("status"),
        },
        "overspend_signal": overspend,
        "forecast_14d_predicted_net": forecast.get("predicted_net") if forecast else None,
        "forecast_30d_ending_savings": forecast.get("ending_savings") if forecast else None,
        "outcome_90d": {
            "savings_delta": (outcome or {}).get("delta", {}).get("savings"),
            "interest_avoided": (outcome or {}).get("delta", {}).get("interest_avoided"),
            "days_safe_delta": (outcome or {}).get("delta", {}).get("days_safe"),
        } if outcome else None,
    }


def _allowed_numbers(snapshot):
    """All numbers Gemini is allowed to mention (as strings, comma-stripped)."""
    out = set()

    def walk(value):
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            n = int(round(value))
            out.add(str(n))
            out.add("{0:,}".format(n))

    walk(snapshot)
    return out


_RUPEE_NUMBER_RE = re.compile(r"(?:Rs\.?|₹)\s*([0-9][0-9,]*)", re.IGNORECASE)
_PERCENT_NUMBER_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*%")


def _validate_briefing(text, snapshot):
    """Reject if the text mentions any rupee or percent number not in the snapshot."""
    if not text:
        return False
    allowed_ints = _allowed_numbers(snapshot)
    for match in _RUPEE_NUMBER_RE.finditer(text):
        candidate = match.group(1).replace(",", "")
        if candidate not in {a.replace(",", "") for a in allowed_ints}:
            return False
    # percentages: allow exact integers from snapshot only
    for match in _PERCENT_NUMBER_RE.finditer(text):
        candidate = match.group(1)
        try:
            n_int = int(round(float(candidate)))
        except ValueError:
            continue
        if str(n_int) not in allowed_ints and str(abs(n_int)) not in allowed_ints:
            # accept small numbers (CV, day counts) — only reject if it looks like a fact
            if n_int >= 5:
                return False
    return True


def _fallback_briefing(snapshot, language):
    """Deterministic fallback if Gemini is unavailable or hallucinates."""
    last7 = snapshot.get("last_7_days", {})
    safety = snapshot.get("safety", {})
    best = snapshot.get("best_day_of_week")
    over = snapshot.get("overspend_signal")
    outcome = snapshot.get("outcome_90d") or {}

    parts = []
    parts.append(
        "{name}, last 7 days you earned Rs {e} and spent Rs {s}.".format(
            name=snapshot.get("user_name") or "Friend",
            e=last7.get("earned", 0),
            s=last7.get("spent", 0),
        )
    )
    if best:
        parts.append("{0} remains your strongest day on average.".format(best))
    if over and over.get("pct_over", 0) >= 15:
        parts.append(
            "{cat} spend is {pct}% above baseline.".format(
                cat=over["category"], pct=over["pct_over"]
            )
        )
    parts.append(
        "You are {d} days safe ({status}).".format(
            d=safety.get("days_safe"), status=safety.get("status")
        )
    )
    if outcome.get("savings_delta") is not None:
        parts.append(
            "Following the GigShield plan: +Rs {s} savings over 90 days.".format(
                s=outcome["savings_delta"]
            )
        )
    return " ".join(parts)


def build_briefing(insights, safety, forecast, outcome, user, *, language="english"):
    snapshot = build_briefing_snapshot(insights, safety, forecast, outcome, user)
    cache_key = (user.get("id"), _snapshot_hash(snapshot, language), language)
    if cache_key in _CACHE:
        return {"text": _CACHE[cache_key], "language": language, "snapshot": snapshot, "source": "cache"}

    label = LANGUAGE_LABEL.get(language, "English")
    prompt = (
        "You are GigShield, a financial copilot for an Indian gig worker.\n"
        "Compose a briefing of EXACTLY 4 sentences in {language_label}.\n\n"
        "Strict rules:\n"
        "- Use ONLY the numbers in the snapshot below. Do not invent or round.\n"
        "- Mention the user by name once.\n"
        "- Order: 1) week summary, 2) one pattern observation, 3) one warning if relevant, "
        "4) one specific number-backed forward-looking statement.\n"
        "- Tone: brief, factual, encouraging — never alarmist.\n"
        "- If language is Hindi or Kannada, use the native script throughout. "
        "Numbers may stay as Arabic numerals.\n"
        "- Output the briefing text only. No preamble, no markdown, no bullets.\n\n"
        "Snapshot:\n{snapshot}\n"
    ).format(language_label=label, snapshot=json.dumps(snapshot, ensure_ascii=False, indent=2))

    raw = (generate_text(prompt) or "").strip()
    raw_lower = raw.lower()
    looks_like_error = (
        not raw
        or "api key" in raw_lower
        or "trouble thinking" in raw_lower
        or "couldn't think" in raw_lower
    )
    if looks_like_error or not _validate_briefing(raw, snapshot):
        text = _fallback_briefing(snapshot, language)
        source = "fallback"
    else:
        text = raw
        source = "gemini"
        _CACHE[cache_key] = text

    return {"text": text, "language": language, "snapshot": snapshot, "source": source}
