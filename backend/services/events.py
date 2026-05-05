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


def ingest_event(store, event, next_id_fn):
    event_type = event.get("type")
    user_id = event.get("user_id")

    if event_type not in EVENT_TYPES:
        return {"error": "unsupported_event_type", "event": event}
    if user_id is None:
        return {"error": "user_id_required", "event": event}

    event_date = event.get("date") or datetime.utcnow().date().isoformat()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    event_record = {
        "id": next_id_fn(store["events"]),
        "user_id": user_id,
        "date": event_date,
        "type": event_type,
        "amount": event.get("amount"),
        "message": event.get("message") or event.get("sms_text"),
        "category": event.get("category"),
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
        sms_text = event.get("sms_text")
        parsed = parse_sms(sms_text) if sms_text else None
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
            "notes": event.get("notes") or "",
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
            "notes": event.get("notes") or "",
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
