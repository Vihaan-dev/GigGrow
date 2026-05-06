"""Click-day anomaly explanation.

When the user clicks a day in the timeline, this service builds a focused
context (the target day's earnings/spending/events + the DOW expectation +
the neighbouring days for trend) and asks Gemini to explain in 2-3 sentences.

Like briefing.py, output is hallucination-guarded: any number Gemini
mentions that doesn't come from the snapshot is rejected and we fall back
to a deterministic template.
"""

import json
import re
from datetime import date, datetime, timedelta

from .gemini_client import generate_text

LANGUAGE_LABEL = {
    "hindi": "Hindi (Devanagari script only)",
    "kannada": "Kannada (Kannada script only)",
    "english": "English",
}

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _classify_anomaly(target_earnings, dow_avg, dow_std):
    if dow_avg <= 0:
        return None
    deviation = target_earnings - dow_avg
    if dow_std > 0:
        z = deviation / dow_std
    else:
        z = 0
    if z >= 1.0:
        return {"kind": "above_expected", "z": round(z, 2)}
    if z <= -1.0:
        return {"kind": "below_expected", "z": round(z, 2)}
    return {"kind": "as_expected", "z": round(z, 2)}


def build_explain_snapshot(insights, target_date_iso, events_by_date):
    daily = insights.get("daily", []) or []
    target = next((d for d in daily if d["date"] == target_date_iso), None)
    if not target:
        return None

    target_dt = _parse_date(target_date_iso)
    dow = target_dt.weekday()
    dow_info = (insights.get("dow_pattern", {}) or {}).get(dow, {})
    dow_avg = dow_info.get("avg", 0)

    # neighbour days (3 before, 3 after) for trend context
    idx = next((i for i, d in enumerate(daily) if d["date"] == target_date_iso), None)
    neighbours = []
    if idx is not None:
        for j in range(max(0, idx - 3), min(len(daily), idx + 4)):
            if j == idx:
                continue
            n = daily[j]
            neighbours.append({
                "date": n["date"],
                "dow": DAY_NAMES[n["dow"]],
                "earnings": n["earnings"],
                "spending": n["spending"],
            })

    # std-dev of same-DOW earnings as a rough sigma
    same_dow_values = [d["earnings"] for d in daily if d["dow"] == dow and d["earnings"] > 0]
    dow_std = 0
    if len(same_dow_values) > 1:
        mean = sum(same_dow_values) / len(same_dow_values)
        var = sum((v - mean) ** 2 for v in same_dow_values) / (len(same_dow_values) - 1)
        dow_std = int(round(var ** 0.5))

    anomaly = _classify_anomaly(target["earnings"], dow_avg, dow_std)

    return {
        "date": target_date_iso,
        "day_of_week": DAY_NAMES[dow],
        "earnings": target["earnings"],
        "spending": target["spending"],
        "spending_breakdown": target.get("spending_by_category", {}),
        "net": target["earnings"] - target["spending"],
        "events_on_day": [e for e in events_by_date.get(target_date_iso, [])],
        "dow_expected_earnings": dow_avg,
        "dow_std_dev": dow_std,
        "anomaly": anomaly,
        "neighbours": neighbours,
    }


def _allowed_numbers(snapshot):
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


def _validate(text, snapshot):
    if not text:
        return False
    allowed = {a.replace(",", "") for a in _allowed_numbers(snapshot)}
    for match in _RUPEE_NUMBER_RE.finditer(text):
        candidate = match.group(1).replace(",", "")
        if candidate not in allowed:
            return False
    return True


def _fallback(snapshot):
    parts = []
    parts.append(
        "{date} ({dow}): earned Rs {e}, spent Rs {s}.".format(
            date=snapshot["date"],
            dow=snapshot["day_of_week"],
            e=snapshot["earnings"],
            s=snapshot["spending"],
        )
    )
    anomaly = snapshot.get("anomaly")
    if anomaly and anomaly["kind"] == "below_expected":
        parts.append(
            "That is below the {dow} average of Rs {avg} (z = {z}σ).".format(
                dow=snapshot["day_of_week"],
                avg=snapshot["dow_expected_earnings"],
                z=anomaly["z"],
            )
        )
    elif anomaly and anomaly["kind"] == "above_expected":
        parts.append(
            "That is above the {dow} average of Rs {avg} (z = {z}σ).".format(
                dow=snapshot["day_of_week"],
                avg=snapshot["dow_expected_earnings"],
                z=anomaly["z"],
            )
        )
    if snapshot.get("events_on_day"):
        parts.append(
            "Events recorded: {0}.".format(", ".join(snapshot["events_on_day"]))
        )
    return " ".join(parts)


def explain_day(insights, events, target_date_iso, language="english"):
    events_by_date = {}
    for evt in events:
        events_by_date.setdefault(evt["date"], []).append(evt.get("type"))

    snapshot = build_explain_snapshot(insights, target_date_iso, events_by_date)
    if not snapshot:
        return {"error": "date_not_in_history"}

    label = LANGUAGE_LABEL.get(language, "English")
    prompt = (
        "You are GigShield, a financial copilot. Explain a single day for an Indian gig worker.\n\n"
        "Strict rules:\n"
        "- Reply in 2 to 3 sentences in {language}.\n"
        "- Use ONLY numbers from the snapshot below. Do not invent.\n"
        "- Cite the day-of-week expectation and any events that happened.\n"
        "- If the day was unusual (anomaly.kind != 'as_expected'), explain WHY using the events on that day.\n"
        "- If language is Hindi or Kannada, use the native script throughout.\n\n"
        "Snapshot:\n{snapshot}\n\n"
        "Output the explanation only. No preamble."
    ).format(language=label, snapshot=json.dumps(snapshot, ensure_ascii=False, indent=2))

    raw = (generate_text(prompt) or "").strip()
    raw_lower = raw.lower()
    looks_like_error = (
        not raw
        or "api key" in raw_lower
        or "trouble thinking" in raw_lower
        or "couldn't think" in raw_lower
    )
    if looks_like_error or not _validate(raw, snapshot):
        text = _fallback(snapshot)
        source = "fallback"
    else:
        text = raw
        source = "gemini"

    return {
        "text": text,
        "language": language,
        "source": source,
        "snapshot": snapshot,
    }
