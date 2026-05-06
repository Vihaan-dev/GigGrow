"""Shared pytest fixtures.

Adds the backend folder to sys.path so tests can import services directly,
and provides a synthetic 30-day dataset that the rest of the suite reuses.
"""

import os
import sys
from datetime import date, timedelta

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture
def thirty_day_dataset():
    """Synthetic Ramesh-like 30-day history. Deterministic, weekend-heavy."""
    end = date(2026, 5, 5)
    earnings = []
    spending = []
    events = []
    for i in range(30):
        d = (end - timedelta(days=29 - i)).isoformat()
        dow = (end - timedelta(days=29 - i)).weekday()
        # Weekend uplift
        amount = 1500 + (i % 4) * 50 if dow >= 4 else 950 + (i % 5) * 40
        earnings.append({"date": d, "amount": amount, "user_id": 1, "deliveries": amount // 200})
        # Daily fuel
        spending.append({"date": d, "amount": 200 + (i % 3) * 20, "category": "fuel", "user_id": 1})
    # One rent + one transfer at month start
    spending.append({"date": (end - timedelta(days=27)).isoformat(), "amount": 7000, "category": "rent", "user_id": 1})
    spending.append({"date": (end - timedelta(days=27)).isoformat(), "amount": 5000, "category": "transfer", "user_id": 1})
    return {"earnings": earnings, "spending": spending, "events": events, "end_date": end}


@pytest.fixture
def ramesh_user():
    return {
        "id": 1,
        "name": "Ramesh",
        "language": "hindi",
        "platform": "swiggy",
        "city": "Whitefield, Bengaluru",
        "occupation": "Delivery partner",
        "goal": "Save for a bike",
        "mandatory_spend": 12000,
        "household_obligation": 5000,
        "current_savings": 13700,
        "age": 29,
        "annual_income": 300000,
        "moneylender_debt": 15000,
        "moneylender_apy": 60,
    }
