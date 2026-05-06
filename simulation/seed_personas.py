"""Seed three demo personas with 30 days of deterministic events each.

Each persona has a distinct financial pattern so judges see GigShield
generalising, not just one user's story.

Run:
    python3 seed_personas.py
    python3 seed_personas.py --base-url http://127.0.0.1:8088   # via API
    python3 seed_personas.py --direct                            # write store.json directly

Personas:
    1. Ramesh   - Swiggy delivery, Bengaluru, weekend-heavy income, fuel overspend
    2. Lakshmi  - Auto driver, Pune, female, surge-on-rain, very volatile
    3. Vikram   - Freelance writer, Bengaluru, lumpy invoice income, mostly zero days
"""

import argparse
import json
import os
import random
import sys
from datetime import date, timedelta
from urllib import request


END_DATE = date(2026, 5, 5)
DAYS = 30


def date_range(end_date=END_DATE, days=DAYS):
    start = end_date - timedelta(days=days - 1)
    return [start + timedelta(days=i) for i in range(days)]


def ramesh_events():
    """Swiggy delivery partner. Weekend-heavy. Low fuel discipline.
    Has a Rs 15,000 moneylender loan at 5%/month (60% APY)."""
    rng = random.Random(101)
    events = []
    fuel_running = 0

    for d in date_range():
        iso = d.isoformat()
        dow = d.weekday()  # 0=Mon

        # Earnings: weekday baseline 800-1200, weekends 1500-2100
        if dow in (4, 5, 6):
            amount = rng.randint(1500, 2100)
            deliveries = max(7, amount // 200)
        elif dow in (0, 1):
            amount = rng.randint(700, 1100)
            deliveries = max(4, amount // 200)
        else:
            amount = rng.randint(900, 1300)
            deliveries = max(5, amount // 200)

        # Occasional rain day: 0.6x earnings
        if rng.random() < 0.13:
            amount = int(amount * 0.6)
            events.append({
                "user_id": 1, "date": iso, "type": "weather_rain",
                "message": "Heavy rain in Whitefield",
            })

        events.append({
            "user_id": 1, "date": iso, "type": "sms_income",
            "amount": amount, "deliveries": deliveries, "platform": "swiggy",
            "sms_text": "Swiggy credit Rs {0} for {1} deliveries".format(amount, deliveries),
        })

        # Fuel: ramps up over the month (the overspend story)
        fuel_amount = rng.randint(140, 240) if d.day < 20 else rng.randint(220, 320)
        fuel_running += fuel_amount
        events.append({
            "user_id": 1, "date": iso, "type": "sms_expense",
            "sms_text": "HDFC: Debit Rs {0} at Sunbeam Petrol Pump, Whitefield".format(fuel_amount),
        })

        # Occasional food
        if rng.random() < 0.4:
            food = rng.randint(80, 220)
            events.append({
                "user_id": 1, "date": iso, "type": "sms_expense",
                "sms_text": "Axis: Debit Rs {0} at A2B Restaurant".format(food),
            })

    # Rent on day 5 of month (one in window: Apr 5? actually April-May window starts Apr 6)
    # Pick the first 5th-of-month in the window
    for d in date_range():
        if d.day == 5:
            events.append({
                "user_id": 1, "date": d.isoformat(), "type": "manual_spend",
                "amount": 7000, "category": "rent", "notes": "Monthly rent",
            })
            events.append({
                "user_id": 1, "date": d.isoformat(), "type": "manual_spend",
                "amount": 5000, "category": "transfer", "notes": "Home transfer",
            })

    return events


def lakshmi_events():
    """Auto driver, Pune. Surge-on-rain (rides spike when raining).
    Female head of household, two school-age kids."""
    rng = random.Random(202)
    events = []

    for d in date_range():
        iso = d.isoformat()
        dow = d.weekday()

        # Base earnings 400-1500, very variable
        amount = rng.randint(350, 1400)
        # Weekends slightly lower (school holiday effect: fewer rush rides)
        if dow in (5, 6):
            amount = int(amount * 0.85)

        # Rain = surge (more rides when people don't want to walk)
        if rng.random() < 0.18:
            amount = int(amount * 1.6)
            events.append({
                "user_id": 2, "date": iso, "type": "surge_bonus",
                "amount": int(amount * 0.2),
                "message": "Rain surge in Hinjewadi corridor",
            })
            events.append({
                "user_id": 2, "date": iso, "type": "weather_rain",
                "message": "Rain in Pune",
            })

        # Occasional very bad day (vehicle issue, illness)
        if rng.random() < 0.07:
            amount = rng.randint(0, 200)
            events.append({
                "user_id": 2, "date": iso, "type": "low_demand",
                "message": "Vehicle servicing morning",
            })

        events.append({
            "user_id": 2, "date": iso, "type": "sms_income",
            "amount": amount, "deliveries": None, "platform": "rapido",
            "sms_text": "Rapido credit Rs {0}".format(amount),
        })

        # CNG fuel daily
        cng = rng.randint(180, 340)
        events.append({
            "user_id": 2, "date": iso, "type": "sms_expense",
            "sms_text": "ICICI: Debit Rs {0} at Indian Oil CNG".format(cng),
        })

        # School-day food (kids tiffin) most weekdays
        if dow < 5 and rng.random() < 0.7:
            food = rng.randint(60, 140)
            events.append({
                "user_id": 2, "date": iso, "type": "sms_expense",
                "sms_text": "Axis: Debit Rs {0} at Apna Bazaar grocery".format(food),
            })

    # Rent on day 1 of month
    for d in date_range():
        if d.day == 1:
            events.append({
                "user_id": 2, "date": d.isoformat(), "type": "manual_spend",
                "amount": 4500, "category": "rent", "notes": "Joint family share",
            })

    # School fees on April 15
    events.append({
        "user_id": 2, "date": "2026-04-15", "type": "manual_spend",
        "amount": 3200, "category": "transfer", "notes": "School fees, daughter",
    })

    return events


def vikram_events():
    """Freelance content writer, HSR Bengaluru. Lumpy invoice income.
    Mostly zero days, then 3-4 big payments per month."""
    rng = random.Random(303)
    events = []

    # Define 4 invoice days with realistic amounts
    invoice_days = ["2026-04-12", "2026-04-22", "2026-04-29", "2026-05-04"]
    invoice_amounts = [8500, 6200, 12000, 4800]

    for d in date_range():
        iso = d.isoformat()
        dow = d.weekday()

        # Most days: zero or tiny platform task income
        if iso in invoice_days:
            idx = invoice_days.index(iso)
            amount = invoice_amounts[idx]
            events.append({
                "user_id": 3, "date": iso, "type": "sms_income",
                "amount": amount, "deliveries": None, "platform": "upwork",
                "sms_text": "HDFC: Credit Rs {0} from Upwork (invoice)".format(amount),
            })
        elif rng.random() < 0.35:
            # Small platform task
            amount = rng.randint(150, 600)
            events.append({
                "user_id": 3, "date": iso, "type": "sms_income",
                "amount": amount, "deliveries": None, "platform": "fiverr",
                "sms_text": "Axis: Credit Rs {0} from Fiverr".format(amount),
            })

        # Daily food (eats out a lot, single, HSR cafes)
        if rng.random() < 0.6:
            food = rng.randint(150, 380)
            events.append({
                "user_id": 3, "date": iso, "type": "sms_expense",
                "sms_text": "ICICI: Debit Rs {0} at Third Wave Coffee, HSR".format(food),
            })

        # Internet/phone occasional
        if d.day == 8 and rng.random() < 0.7:
            events.append({
                "user_id": 3, "date": iso, "type": "sms_expense",
                "sms_text": "HDFC: Debit Rs 599 at Airtel recharge",
            })

    # Rent on day 3
    for d in date_range():
        if d.day == 3:
            events.append({
                "user_id": 3, "date": d.isoformat(), "type": "manual_spend",
                "amount": 11000, "category": "rent", "notes": "1BHK HSR Layout",
            })

    return events


PERSONAS = [
    {
        "user": {
            "id": 1,
            "name": "Ramesh",
            "language": "hindi",
            "platform": "swiggy",
            "city": "Whitefield, Bengaluru",
            "occupation": "Delivery partner",
            "goal": "Save Rs 22,000 for a second-hand bike",
            "mandatory_spend": 12000,
            "household_obligation": 5000,
            "current_savings": 13700,
            "age": 29,
            "annual_income": 300000,
            "moneylender_debt": 15000,
            "moneylender_apy": 60,
        },
        "events": ramesh_events,
    },
    {
        "user": {
            "id": 2,
            "name": "Lakshmi",
            "language": "hindi",
            "platform": "rapido",
            "city": "Hinjewadi, Pune",
            "occupation": "Auto driver",
            "goal": "Rs 35,000 for daughter's school admission by August",
            "mandatory_spend": 8000,
            "household_obligation": 0,
            "current_savings": 6500,
            "age": 34,
            "annual_income": 240000,
            "moneylender_debt": 8000,
            "moneylender_apy": 48,
        },
        "events": lakshmi_events,
    },
    {
        "user": {
            "id": 3,
            "name": "Vikram",
            "language": "english",
            "platform": "upwork",
            "city": "HSR Layout, Bengaluru",
            "occupation": "Freelance writer",
            "goal": "Build a 6-month buffer to focus on long-form work",
            "mandatory_spend": 15000,
            "household_obligation": 0,
            "current_savings": 22000,
            "age": 26,
            "annual_income": 360000,
            "moneylender_debt": 0,
            "moneylender_apy": 0,
        },
        "events": vikram_events,
    },
]


def seed_via_api(base_url):
    """Hit the live API. Useful when backend is running."""
    base = base_url.rstrip("/")

    def post(path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            base + path,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    post("/api/reset", {})
    print("✓ store reset")

    for p in PERSONAS:
        post("/api/users", {k: v for k, v in p["user"].items() if k != "id"})
        events = p["events"]()
        post("/api/events/ingest", {"events": events})
        print("✓ seeded {0} ({1} events)".format(p["user"]["name"], len(events)))


def seed_direct():
    """Write store.json directly (no server needed)."""
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.normpath(os.path.join(here, "..", "backend"))
    sys.path.insert(0, backend_dir)
    from storage import update_store, get_store_path  # type: ignore
    from services.events import ingest_event  # type: ignore

    def updater(store):
        store["users"] = []
        store["earnings"] = []
        store["spending"] = []
        store["events"] = []
        for p in PERSONAS:
            store["users"].append(p["user"])
        return None

    update_store(updater)

    def next_id(items):
        if not items:
            return 1
        return max(item.get("id", 0) for item in items) + 1

    def ingest_updater(store):
        for p in PERSONAS:
            for evt in p["events"]():
                ingest_event(store, evt, next_id)
        return None

    update_store(ingest_updater)

    with open(get_store_path()) as f:
        final = json.load(f)
    print("users:    ", len(final["users"]))
    print("earnings: ", len(final["earnings"]))
    print("spending: ", len(final["spending"]))
    print("events:   ", len(final["events"]))
    for u in final["users"]:
        print("  - {0} (id={1}): savings={2}, debt={3} @ {4}%".format(
            u["name"], u["id"], u["current_savings"],
            u.get("moneylender_debt", 0), u.get("moneylender_apy", 0)
        ))


def main():
    parser = argparse.ArgumentParser(description="Seed GigShield demo personas")
    parser.add_argument("--base-url", default=None, help="If set, seed via the live API")
    parser.add_argument("--direct", action="store_true", help="Write store.json directly")
    args = parser.parse_args()

    if args.base_url:
        seed_via_api(args.base_url)
    else:
        seed_direct()


if __name__ == "__main__":
    main()
