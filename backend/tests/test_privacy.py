"""Tests guarding the privacy / data-minimalism contract.

These are arguably the most important tests in the suite — if they break
silently, our public claim ('no raw SMS stored') becomes false.
"""

import json

from services.events import ingest_event, _redact


def _make_store():
    return {"users": [{"id": 1}], "earnings": [], "spending": [], "events": []}


def _next_id(items):
    return (max((i.get("id", 0) for i in items), default=0)) + 1


def _store_dump_lower(store):
    return json.dumps(store).lower()


def test_sms_event_does_not_persist_raw_text():
    store = _make_store()
    raw = "HDFC: Debit Rs 600 at Sunbeam Petrol Pump, Whitefield. Bal Rs 4200"
    ingest_event(store, {
        "user_id": 1, "date": "2026-04-10", "type": "sms_expense",
        "sms_text": raw,
    }, _next_id)
    dump = _store_dump_lower(store)
    # Framing markers from the SMS itself must not appear anywhere in the store
    assert "hdfc:" not in dump
    assert "debit rs" not in dump
    assert "bal rs" not in dump
    assert "whitefield" not in dump
    # But the parsed merchant and amount may persist
    spend = store["spending"][0]
    assert spend["amount"] == 600
    assert spend["category"] == "fuel"
    assert spend["merchant"] == "Sunbeam Petrol Pump"


def test_non_sms_summary_is_redacted():
    store = _make_store()
    ingest_event(store, {
        "user_id": 1, "date": "2026-04-10", "type": "weather_rain",
        "message": "Heavy rain near 411057, contact +91 9876543210 for vehicle help",
    }, _next_id)
    summary = store["events"][0]["summary"]
    assert "411057" not in summary
    assert "9876543210" not in summary
    assert "###" in summary  # phone/account redaction marker


def test_non_sms_summary_truncated_to_max_length():
    long_msg = "x" * 200
    redacted = _redact(long_msg, max_len=80)
    assert len(redacted) <= 81  # 80 + ellipsis


def test_sms_event_has_no_summary_field_filled():
    store = _make_store()
    ingest_event(store, {
        "user_id": 1, "date": "2026-04-10", "type": "sms_income",
        "sms_text": "Swiggy credit Rs 1240",
        "amount": 1240,
        "platform": "swiggy",
    }, _next_id)
    # Summary should be None for SMS events; only parsed structured fields persist
    assert store["events"][0]["summary"] is None
