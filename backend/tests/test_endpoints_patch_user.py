"""End-to-end tests for PATCH /api/users/<uid>."""

import sys

import pytest


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    store_path = tmp_path / "store.json"
    monkeypatch.setenv("DATA_FILE", str(store_path))

    for mod in list(sys.modules.keys()):
        if mod.startswith("storage") or mod == "app":
            del sys.modules[mod]

    import app as gigshield  # noqa: WPS433
    client = gigshield.app.test_client()

    client.post("/api/users", json={
        "name": "Test", "language": "english", "platform": "swiggy",
        "mandatory_spend": 12000, "household_obligation": 0,
        "current_savings": 5000, "age": 30, "annual_income": 200000,
    })
    return client


def test_patch_updates_mandatory_spend(isolated_app):
    r = isolated_app.patch("/api/users/1", json={"mandatory_spend": 14000}).get_json()
    assert r["user"]["mandatory_spend"] == 14000
    assert r["updated_fields"] == ["mandatory_spend"]


def test_patch_updates_multiple_fields_at_once(isolated_app):
    r = isolated_app.patch("/api/users/1", json={
        "mandatory_spend": 11000,
        "current_savings": 8000,
        "moneylender_debt": 5000,
        "moneylender_apy": 36,
    }).get_json()
    user = r["user"]
    assert user["mandatory_spend"] == 11000
    assert user["current_savings"] == 8000
    assert user["moneylender_debt"] == 5000
    assert user["moneylender_apy"] == 36
    assert set(r["updated_fields"]) == {
        "mandatory_spend", "current_savings", "moneylender_debt", "moneylender_apy"
    }


def test_patch_ignores_unknown_field(isolated_app):
    # name + an unknown 'admin' flag
    r = isolated_app.patch("/api/users/1", json={
        "name": "Updated",
        "admin": True,            # not on the editable list, should be ignored
        "is_premium": True,       # ditto
    }).get_json()
    assert r["updated_fields"] == ["name"]
    assert "admin" not in r["user"]
    assert "is_premium" not in r["user"]


def test_patch_rejects_invalid_age(isolated_app):
    r = isolated_app.patch("/api/users/1", json={"age": 0})
    assert r.status_code == 400


def test_patch_rejects_invalid_apy(isolated_app):
    r = isolated_app.patch("/api/users/1", json={"moneylender_apy": 200})
    assert r.status_code == 400


def test_patch_rejects_negative_savings(isolated_app):
    r = isolated_app.patch("/api/users/1", json={"current_savings": -50})
    assert r.status_code == 400


def test_patch_unknown_user_404(isolated_app):
    r = isolated_app.patch("/api/users/999", json={"mandatory_spend": 5000})
    assert r.status_code == 404


def test_patch_no_editable_fields_400(isolated_app):
    r = isolated_app.patch("/api/users/1", json={"admin": True})
    assert r.status_code == 400


def test_patch_invalid_language_falls_back_to_existing(isolated_app):
    # `normalize_language` returns the previous language for unknown values.
    r = isolated_app.patch("/api/users/1", json={"language": "klingon"}).get_json()
    assert r["user"]["language"] == "english"  # original value preserved
