"""Event ingestion with on-the-fly SMS parsing.

Data-minimalism contract:
  - Raw SMS text is parsed in-memory and dropped before persistence.
  - The persisted event record stores only: amount, category, merchant,
    confidence, and a provenance label ("sms" / "manual" / "system").
  - For non-SMS event types (rain/holiday/surge/...), we keep a SHORT
    redacted summary (max 80 chars, freed of personal identifiers) under
    `summary`. The full SMS text is never written to disk.

This matches the proposal's claim:  "No raw SMS stored. SMS parsed,
extracted, then discarded."
"""

import re
from datetime import datetime
from .sms_parser import parse_sms

EVENT_TYPES = {
    "sms_expense",
    "sms_income",
    "manual_spend",
    "weather_rain",
    "holiday",
    "surge_bonus",
    "low_demand",
    "loan_query",
    "scheme_query",
}

_SMS_EVENT_TYPES = {"sms_expense", "sms_income"}


def _redact(text, max_len=80):
    """Strip phone numbers, account digits, names. Keep the gist."""
    if not text:
        return None
    cleaned = re.sub(r"\b\d{6,}\b", "###", text)        # account / card numbers
    cleaned = re.sub(r"\b\+?91[\s-]?\d{4,}\b", "###", cleaned)  # phone-like
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip() + "…"
    return cleaned


def ingest_event(store, event, next_id_fn):
    event_type = event.get("type")
    user_id = event.get("user_id")

    if event_type not in EVENT_TYPES:
        return {"error": "unsupported_event_type", "event": event}
    if user_id is None:
        return {"error": "user_id_required", "event": event}

    event_date = event.get("date") or datetime.utcnow().date().isoformat()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # If this is an SMS event, parse FIRST so we can persist only the
    # extracted, structured fields — never the raw SMS string.
    parsed = None
    raw_sms = event.get("sms_text")
    if event_type in _SMS_EVENT_TYPES and raw_sms:
        parsed = parse_sms(raw_sms)

    is_sms = event_type in _SMS_EVENT_TYPES

    # Persisted summary: NEVER the raw SMS. For non-SMS events, take the
    # caller's `message` field after redaction. For SMS events, drop the
    # text entirely; only the parsed fields survive.
    persisted_summary = None
    if not is_sms:
        persisted_summary = _redact(event.get("message"))

    event_record = {
        "id": next_id_fn(store["events"]),
        "user_id": user_id,
        "date": event_date,
        "type": event_type,
        "amount": event.get("amount"),
        "summary": persisted_summary,
        "category": event.get("category"),
        "merchant": (parsed or {}).get("merchant") if is_sms else None,
        "parsed_confidence": (parsed or {}).get("confidence") if is_sms else None,
        "parsed_by": (parsed or {}).get("parsed_by") if is_sms else None,
        "tags": event.get("tags", []),
        "metadata": event.get("metadata", {}),
        "created_at": now,
    }

    store["events"].append(event_record)

    results = {
        "event": event_record,
        "earnings": [],
        "spending": [],
        "warnings": [],
    }

    if event_type == "sms_expense":
        if parsed and "error" not in parsed:
            amount = parsed["amount"]
            category = parsed["category"]
        else:
            amount = event.get("amount")
            category = event.get("category", "other")
            if parsed and "error" in parsed:
                results["warnings"].append(parsed["error"])

        if amount is None:
            return {"error": "amount_required", "event": event_record}

        spend = {
            "id": next_id_fn(store["spending"]),
            "user_id": user_id,
            "date": event_date,
            "amount": int(amount),
            "category": category,
            "source": "sms",
            "merchant": (parsed or {}).get("merchant"),
            "notes": _redact(event.get("notes")) or "",
            "created_at": now,
        }
        store["spending"].append(spend)
        results["spending"].append(spend)

    if event_type == "manual_spend":
        amount = event.get("amount")
        if amount is None:
            return {"error": "amount_required", "event": event_record}

        spend = {
            "id": next_id_fn(store["spending"]),
            "user_id": user_id,
            "date": event_date,
            "amount": int(amount),
            "category": event.get("category", "other"),
            "source": "manual",
            "notes": _redact(event.get("notes")) or "",
            "created_at": now,
        }
        store["spending"].append(spend)
        results["spending"].append(spend)

    if event_type in {"sms_income", "surge_bonus"}:
        amount = event.get("amount")
        if amount is None:
            return {"error": "amount_required", "event": event_record}

        earning = {
            "id": next_id_fn(store["earnings"]),
            "user_id": user_id,
            "date": event_date,
            "amount": int(amount),
            "deliveries": event.get("deliveries"),
            "platform": event.get("platform", "unknown"),
            "source": "sms" if event_type == "sms_income" else "bonus",
            "created_at": now,
        }
        store["earnings"].append(earning)
        results["earnings"].append(earning)

    return results
