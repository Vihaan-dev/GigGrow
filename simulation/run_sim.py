import argparse
import copy
import json
import os
import sys
from datetime import datetime, timedelta
from urllib import request, error

DEFAULT_BASE_URL = os.getenv("SIM_API_BASE", "http://127.0.0.1:8000")
DEFAULT_DATA_PATH = os.getenv(
    "SIM_DATA_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "events.json"),
)


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("invalid_date_format")


def load_events(path):
    with open(path, "r") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        return payload.get("events", []), payload.get("meta", {})
    return payload, {}


def filter_events(events, start_date=None, end_date=None):
    if start_date is None and end_date is None:
        return list(events)

    results = []
    for event in events:
        event_date = parse_date(event["date"])
        if start_date and event_date < start_date:
            continue
        if end_date and event_date > end_date:
            continue
        results.append(event)
    return results


def enrich_events(events, user_id, default_user_id):
    enriched = []
    fallback_user_id = user_id or default_user_id or 1

    for event in events:
        updated = copy.deepcopy(event)
        updated["user_id"] = user_id or updated.get("user_id") or fallback_user_id
        enriched.append(updated)

    return enriched


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    with request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def seed_user(base_url, payload):
    url = base_url.rstrip("/") + "/api/users"
    return post_json(url, payload)


def ingest_events(base_url, events):
    url = base_url.rstrip("/") + "/api/events/ingest"
    return post_json(url, {"events": events})


def summarize_events(events):
    if not events:
        return "no events"
    dates = sorted({event["date"] for event in events})
    return "{0} events from {1} to {2}".format(len(events), dates[0], dates[-1])


def run_simulation(args):
    events, meta = load_events(args.data)
    default_user_id = meta.get("default_user_id")

    if args.command == "list-dates":
        dates = sorted({event["date"] for event in events})
        print("\n".join(dates))
        return

    if args.command == "seed-user":
        payload = {
            "name": args.name,
            "language": args.language,
            "platform": args.platform,
            "mandatory_spend": args.mandatory_spend,
            "household_obligation": args.household_obligation,
            "current_savings": args.current_savings,
            "age": args.age,
            "annual_income": args.annual_income,
        }
        response = seed_user(args.base_url, payload)
        print(json.dumps(response, indent=2))
        return

    if args.command == "simulate-day":
        start_date = parse_date(args.date)
        end_date = start_date
    elif args.command == "simulate-week":
        start_date = parse_date(args.start)
        end_date = start_date + timedelta(days=6)
    elif args.command == "simulate-month":
        start_date = parse_date(args.start)
        end_date = start_date + timedelta(days=args.days - 1)
    elif args.command == "simulate-range":
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    elif args.command == "simulate-all":
        start_date = None
        end_date = None
    else:
        raise ValueError("unknown_command")

    selected = filter_events(events, start_date, end_date)
    selected = enrich_events(selected, args.user_id, default_user_id)

    if args.dry_run:
        print(summarize_events(selected))
        return

    response = ingest_events(args.base_url, selected)
    print("Sent {0} events".format(response.get("count", 0)))


def build_parser():
    parser = argparse.ArgumentParser(description="GigShield simulation runner")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--data", default=DEFAULT_DATA_PATH)
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    seed = subparsers.add_parser("seed-user")
    seed.add_argument("--name", default="Ramesh")
    seed.add_argument("--language", default="hindi")
    seed.add_argument("--platform", default="swiggy")
    seed.add_argument("--mandatory-spend", dest="mandatory_spend", default=12000, type=int)
    seed.add_argument("--household-obligation", dest="household_obligation", default=5000, type=int)
    seed.add_argument("--current-savings", dest="current_savings", default=3200, type=int)
    seed.add_argument("--age", default=29, type=int)
    seed.add_argument("--annual-income", dest="annual_income", default=300000, type=int)

    list_dates = subparsers.add_parser("list-dates")
    list_dates.set_defaults(command="list-dates")

    simulate_day = subparsers.add_parser("simulate-day")
    simulate_day.add_argument("--date", required=True)

    simulate_week = subparsers.add_parser("simulate-week")
    simulate_week.add_argument("--start", required=True)

    simulate_month = subparsers.add_parser("simulate-month")
    simulate_month.add_argument("--start", required=True)
    simulate_month.add_argument("--days", default=30, type=int)

    simulate_range = subparsers.add_parser("simulate-range")
    simulate_range.add_argument("--start", required=True)
    simulate_range.add_argument("--end", required=True)

    simulate_all = subparsers.add_parser("simulate-all")
    simulate_all.set_defaults(command="simulate-all")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_simulation(args)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        print("HTTP error {0}: {1}".format(exc.code, payload))
        sys.exit(1)
    except Exception as exc:
        print("Simulation failed: {0}".format(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
