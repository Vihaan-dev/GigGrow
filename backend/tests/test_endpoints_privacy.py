"""End-to-end tests for /api/export and /api/forget."""

import os
import sys
import tempfile
import json
import pytest


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Run the Flask app against a temp store.json so tests don't touch real data."""
    store_path = tmp_path / "store.json"
    monkeypatch.setenv("DATA_FILE", str(store_path))

    # Reload modules that read DATA_FILE at import time
    for mod in list(sys.modules.keys()):
        if mod.startswith("storage") or mod == "app":
            del sys.modules[mod]

    import app as gigshield  # noqa: WPS433
    client = gigshield.app.test_client()

    # Seed a single user with one SMS event
    client.post("/api/users", json={
        "name": "Test", "language": "english", "platform": "swiggy",
        "mandatory_spend": 12000, "household_obligation": 0,
        "current_savings": 5000, "age": 30, "annual_income": 200000,
    })
    client.post("/api/events/ingest", json={"events": [
        {"user_id": 1, "date": "2026-04-10", "type": "sms_income",
         "amount": 1200, "platform": "swiggy",
         "sms_text": "Swiggy credit Rs 1200"},
    ]})
    return client


def test_export_returns_user_data(isolated_app):
    r = isolated_app.get("/api/export/1").get_json()
    assert "user" in r
    assert r["user"]["name"] == "Test"
    assert "earnings" in r
    assert len(r["earnings"]) == 1
    assert "data_minimalism_note" in r


def test_export_unknown_user_404(isolated_app):
    r = isolated_app.get("/api/export/999")
    assert r.status_code == 404


def test_forget_requires_confirmation_phrase(isolated_app):
    r = isolated_app.post("/api/forget/1", json={"confirm": "wrong"})
    assert r.status_code == 400


def test_forget_wipes_data_keeps_user(isolated_app):
    r = isolated_app.post("/api/forget/1", json={"confirm": "I confirm"}).get_json()
    assert r["removed"]["earnings"] >= 1
    assert r["user_record_kept"] is True
    # Verify wiped
    state = isolated_app.get("/api/state/1").get_json()
    assert state["totals"]["earnings"] == 0
    assert state["totals"]["spending"] == 0


def test_forget_hard_removes_user_too(isolated_app):
    r = isolated_app.post("/api/forget/1", json={"confirm": "I confirm", "hard": True}).get_json()
    assert r["user_record_kept"] is False
    follow = isolated_app.get("/api/state/1")
    assert follow.status_code == 404
