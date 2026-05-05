from datetime import date
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from storage import read_store, update_store, next_id
from services.sms_parser import parse_sms
from services.safety import calculate_safety_buffer, check_safety_status
from services.analytics import build_daily_summary
from services.schemes import match_schemes, SCHEMES
from services.loans import match_loans, LOANS
from services.gemini_client import generate_text
from services.events import ingest_event
from services.profile_insights import build_profile_insights
from services.forecast import forecast_days, forecast_with_purchase
from services.nudges import build_nudges
from services.crisis import assess_crisis

load_dotenv()

app = Flask(__name__)
CORS(app)

ALLOWED_LANGUAGES = {"english", "hindi", "kannada"}


def json_error(message, status=400):
    return jsonify({"error": message}), status


def get_json():
    if not request.is_json:
        return None
    return request.get_json(silent=True)


def require_fields(data, fields):
    missing = [field for field in fields if field not in data]
    return missing


def parse_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_{0}".format(field_name))


def parse_int_optional(value, field_name, default=0):
    if value is None or value == "":
        return default
    return parse_int(value, field_name)


def normalize_language(value, default="hindi"):
    language = str(value or "").strip().lower()
    if language in ALLOWED_LANGUAGES:
        return language
    return default


def find_user(store, user_id):
    for user in store.get("users", []):
        if user.get("id") == user_id:
            return user
    return None


def filter_by_user(items, user_id):
    return [item for item in items if item.get("user_id") == user_id]


@app.get("/health")
def health():
    return {"status": "ok", "service": "gigshield"}


@app.post("/api/reset")
def reset_data():
    """Clear all data and reset store to empty state."""
    def updater(store):
        store["users"] = []
        store["earnings"] = []
        store["spending"] = []
        store["events"] = []
        return {"status": "reset"}
    
    result = update_store(updater)
    return jsonify(result), 200


@app.post("/api/users")
def create_user():
    data = get_json()
    if data is None:
        return json_error("json_required")

    required = ["name", "language", "platform", "mandatory_spend", "household_obligation"]
    missing = require_fields(data, required)
    if missing:
        return json_error("missing_fields: {0}".format(",".join(missing)))

    try:
        mandatory_spend = parse_int(data["mandatory_spend"], "mandatory_spend")
        household_obligation = parse_int(data["household_obligation"], "household_obligation")
        current_savings = parse_int_optional(data.get("current_savings"), "current_savings", 0)
        age = parse_int_optional(data.get("age"), "age", 0)
        annual_income = parse_int_optional(data.get("annual_income"), "annual_income", 0)
        language = normalize_language(data.get("language"))
    except ValueError as exc:
        return json_error(str(exc))

    def updater(store):
        user_id = next_id(store["users"])
        user = {
            "id": user_id,
            "name": data["name"],
            "language": language,
            "platform": data["platform"],
            "mandatory_spend": mandatory_spend,
            "household_obligation": household_obligation,
            "current_savings": current_savings,
            "age": age,
            "annual_income": annual_income,
        }
        store["users"].append(user)
        return user

    user = update_store(updater)
    return jsonify(user), 201


@app.get("/api/users/<int:user_id>")
def get_user(user_id):
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)
    return jsonify(user)


@app.post("/api/earnings/log")
def log_earning():
    data = get_json()
    if data is None:
        return json_error("json_required")

    required = ["user_id", "date", "amount"]
    missing = require_fields(data, required)
    if missing:
        return json_error("missing_fields: {0}".format(",".join(missing)))

    try:
        user_id = parse_int(data["user_id"], "user_id")
        amount = parse_int(data["amount"], "amount")
        deliveries = parse_int_optional(data.get("deliveries"), "deliveries", None)
    except ValueError as exc:
        return json_error(str(exc))

    def updater(store):
        user = find_user(store, user_id)
        if not user:
            raise ValueError("user_not_found")

        earning = {
            "id": next_id(store["earnings"]),
            "user_id": user_id,
            "date": data["date"],
            "amount": amount,
            "deliveries": deliveries,
            "platform": data.get("platform", user.get("platform", "unknown")),
            "source": data.get("source", "manual"),
        }
        store["earnings"].append(earning)
        return earning

    try:
        earning = update_store(updater)
    except ValueError:
        return json_error("user_not_found", 404)

    return jsonify({"status": "logged", "earning": earning})


@app.get("/api/earnings/<int:user_id>")
def get_earnings(user_id):
    try:
        days = parse_int(request.args.get("days", 30), "days")
    except ValueError as exc:
        return json_error(str(exc))
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings = filter_by_user(store.get("earnings", []), user_id)
    earnings = sorted(earnings, key=lambda item: item["date"], reverse=True)

    return jsonify({
        "user_id": user_id,
        "count": len(earnings[:days]),
        "earnings": earnings[:days],
    })


@app.post("/api/spending/log")
def log_spending():
    data = get_json()
    if data is None:
        return json_error("json_required")

    required = ["user_id", "date", "amount", "category"]
    missing = require_fields(data, required)
    if missing:
        return json_error("missing_fields: {0}".format(",".join(missing)))

    try:
        user_id = parse_int(data["user_id"], "user_id")
        amount = parse_int(data["amount"], "amount")
    except ValueError as exc:
        return json_error(str(exc))

    def updater(store):
        user = find_user(store, user_id)
        if not user:
            raise ValueError("user_not_found")

        spend = {
            "id": next_id(store["spending"]),
            "user_id": user_id,
            "date": data["date"],
            "amount": amount,
            "category": data["category"],
            "source": data.get("source", "manual"),
            "notes": data.get("notes", ""),
        }
        store["spending"].append(spend)
        return spend

    try:
        spend = update_store(updater)
    except ValueError:
        return json_error("user_not_found", 404)

    return jsonify({"status": "logged", "spending": spend})


@app.post("/api/spending/parse-sms")
def parse_sms_endpoint():
    data = get_json()
    if data is None:
        return json_error("json_required")

    required = ["user_id", "sms_text"]
    missing = require_fields(data, required)
    if missing:
        return json_error("missing_fields: {0}".format(",".join(missing)))

    parsed = parse_sms(data["sms_text"])
    if "error" in parsed:
        return json_error(parsed["error"], 400)

    try:
        user_id = parse_int(data["user_id"], "user_id")
    except ValueError as exc:
        return json_error(str(exc))
    spend_date = data.get("date", date.today().isoformat())

    def updater(store):
        user = find_user(store, user_id)
        if not user:
            raise ValueError("user_not_found")

        spend = {
            "id": next_id(store["spending"]),
            "user_id": user_id,
            "date": spend_date,
            "amount": int(parsed["amount"]),
            "category": parsed["category"],
            "source": "sms",
            "notes": parsed.get("notes", ""),
        }
        store["spending"].append(spend)
        return spend

    try:
        spend = update_store(updater)
    except ValueError:
        return json_error("user_not_found", 404)

    return jsonify({
        "status": "parsed_and_saved",
        "result": parsed,
        "spending": spend,
    })


@app.get("/api/spending/<int:user_id>")
def get_spending(user_id):
    try:
        days = parse_int(request.args.get("days", 30), "days")
    except ValueError as exc:
        return json_error(str(exc))
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    spending = filter_by_user(store.get("spending", []), user_id)
    spending = sorted(spending, key=lambda item: item["date"], reverse=True)

    by_category = {}
    for item in spending[: days * 7]:
        cat = item.get("category", "other")
        by_category[cat] = by_category.get(cat, 0) + item.get("amount", 0)

    return jsonify({
        "user_id": user_id,
        "count": len(spending[: days * 7]),
        "by_category": by_category,
        "spending": spending[: days * 7],
    })


@app.post("/api/events/ingest")
def ingest_events():
    data = get_json()
    if data is None:
        return json_error("json_required")

    if isinstance(data, list):
        events = data
    else:
        events = data.get("events") or [data]

    def updater(store):
        results = []
        for event in events:
            try:
                user_id = parse_int(event.get("user_id"), "user_id")
            except ValueError:
                results.append({"error": "invalid_user_id", "event": event})
                continue

            if not find_user(store, user_id):
                results.append({"error": "user_not_found", "event": event})
                continue

            event["user_id"] = user_id
            result = ingest_event(store, event, next_id)
            results.append(result)
        return results

    results = update_store(updater)
    return jsonify({"count": len(results), "results": results})


@app.get("/api/events/<int:user_id>")
def get_events(user_id):
    try:
        days = parse_int(request.args.get("days", 30), "days")
    except ValueError as exc:
        return json_error(str(exc))
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    events = filter_by_user(store.get("events", []), user_id)
    events = sorted(events, key=lambda item: item["date"], reverse=True)

    return jsonify({
        "user_id": user_id,
        "count": len(events[:days]),
        "events": events[:days],
    })


@app.get("/api/safety/<int:user_id>")
def get_safety(user_id):
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings = filter_by_user(store.get("earnings", []), user_id)
    earnings = sorted(earnings, key=lambda item: item["date"], reverse=True)
    earnings_values = [item["amount"] for item in earnings[:30]]

    mandatory_daily = user["mandatory_spend"] / 7

    buffer_info = calculate_safety_buffer(earnings_values, mandatory_daily)
    if "error" in buffer_info:
        return json_error(buffer_info["error"], 400)

    status = check_safety_status(user.get("current_savings", 0), mandatory_daily)

    return jsonify({
        "user_id": user_id,
        "current_savings": user.get("current_savings", 0),
        "days_safe": status["days_safe"],
        "status": status["status"],
        "buffer_info": buffer_info,
        "recommendation": "Target buffer: {0} (30 days safe)".format(
            buffer_info["recommended_buffer"]
        ),
    })


@app.get("/api/summary/<int:user_id>")
def get_summary(user_id):
    try:
        days = parse_int(request.args.get("days", 30), "days")
    except ValueError as exc:
        return json_error(str(exc))
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings = filter_by_user(store.get("earnings", []), user_id)
    spending = filter_by_user(store.get("spending", []), user_id)
    events = filter_by_user(store.get("events", []), user_id)

    summary = build_daily_summary(earnings, spending, events, days=days)
    return jsonify(summary)


@app.get("/api/state/<int:user_id>")
def get_state(user_id):
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings = filter_by_user(store.get("earnings", []), user_id)
    spending = filter_by_user(store.get("spending", []), user_id)
    events = filter_by_user(store.get("events", []), user_id)

    summary = build_daily_summary(earnings, spending, events, days=30)

    mandatory_daily = user["mandatory_spend"] / 7
    earnings_values = [item["amount"] for item in sorted(
        earnings, key=lambda item: item["date"], reverse=True
    )[:30]]

    buffer_info = calculate_safety_buffer(earnings_values, mandatory_daily)
    safety = check_safety_status(user.get("current_savings", 0), mandatory_daily)

    return jsonify({
        "user": user,
        "summary": summary,
        "safety": safety,
        "buffer_info": buffer_info if "error" not in buffer_info else None,
        "totals": {
            "earnings": sum(item.get("amount", 0) for item in earnings),
            "spending": sum(item.get("amount", 0) for item in spending),
        },
    })


@app.post("/api/schemes/match")
def match_user_schemes():
    data = get_json()
    if data is None:
        return json_error("json_required")

    profile = {}
    if "user_id" in data:
        try:
            user_id = parse_int(data["user_id"], "user_id")
        except ValueError as exc:
            return json_error(str(exc))
        store = read_store()
        user = find_user(store, user_id)
        if not user:
            return json_error("user_not_found", 404)
        profile = {
            "annual_income": user.get("annual_income", 0),
            "age": user.get("age", 0),
        }
    else:
        try:
            profile = {
                "annual_income": parse_int_optional(data.get("annual_income"), "annual_income", 0),
                "age": parse_int_optional(data.get("age"), "age", 0),
            }
        except ValueError as exc:
            return json_error(str(exc))

    matched = match_schemes(profile)
    return jsonify({
        "matched_count": len(matched),
        "schemes": matched,
    })


@app.get("/api/schemes/all")
def get_all_schemes():
    return jsonify({"count": len(SCHEMES), "schemes": SCHEMES})


@app.post("/api/loans/match")
def match_user_loans():
    data = get_json()
    if data is None:
        return json_error("json_required")

    amount = data.get("amount")
    try:
        amount_value = parse_int_optional(amount, "amount", None)
    except ValueError as exc:
        return json_error(str(exc))

    profile = {}
    if "user_id" in data:
        try:
            user_id = parse_int(data["user_id"], "user_id")
        except ValueError as exc:
            return json_error(str(exc))
        store = read_store()
        user = find_user(store, user_id)
        if not user:
            return json_error("user_not_found", 404)
        profile = {
            "annual_income": user.get("annual_income", 0),
        }
    else:
        try:
            profile = {
                "annual_income": parse_int_optional(data.get("annual_income"), "annual_income", 0),
            }
        except ValueError as exc:
            return json_error(str(exc))

    matched = match_loans(profile, amount=amount_value)
    return jsonify({
        "matched_count": len(matched),
        "loans": matched,
    })


@app.get("/api/loans/all")
def get_all_loans():
    return jsonify({"count": len(LOANS), "loans": LOANS})


@app.post("/api/chat")
def chat():
    data = get_json()
    if data is None:
        return json_error("json_required")

    required = ["user_id", "message"]
    missing = require_fields(data, required)
    if missing:
        return json_error("missing_fields: {0}".format(",".join(missing)))

    try:
        user_id = parse_int(data["user_id"], "user_id")
    except ValueError as exc:
        return json_error(str(exc))

    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    language = normalize_language(data.get("language"), normalize_language(user.get("language"), "hindi"))

    earnings = filter_by_user(store.get("earnings", []), user_id)
    spending = filter_by_user(store.get("spending", []), user_id)
    events = filter_by_user(store.get("events", []), user_id)

    summary = build_daily_summary(earnings, spending, events, days=7)
    spending_total = sum(item.get("amount", 0) for item in spending)
    earnings_total = sum(item.get("amount", 0) for item in earnings)

    prompt = (
        "You are a financial copilot for gig workers in India. "
        "Respond in {language}. Keep it short and actionable.\n\n"
        "User message: {message}\n\n"
        "User data:\n"
        "- Current savings: {savings}\n"
        "- Total earnings: {earnings}\n"
        "- Total spending: {spending}\n"
        "- Projected month earnings: {projected}\n"
        "- Recent day types: {day_types}\n\n"
        "Respond in 2-3 sentences. If language is Hindi or Kannada, avoid English words."
    ).format(
        language=language,
        message=data["message"],
        savings=user.get("current_savings", 0),
        earnings=earnings_total,
        spending=spending_total,
        projected=summary.get("projected_month_earnings", 0),
        day_types=[day["day_type"] for day in summary.get("days", [])[-3:]],
    )

    response_text = generate_text(prompt)

    return jsonify({
        "response": response_text,
        "language": language,
    })


def _user_dataset(store, user_id):
    earnings = filter_by_user(store.get("earnings", []), user_id)
    spending = filter_by_user(store.get("spending", []), user_id)
    events = filter_by_user(store.get("events", []), user_id)
    return earnings, spending, events


@app.get("/api/insights/<int:user_id>")
def get_insights(user_id):
    try:
        days = parse_int(request.args.get("days", 30), "days")
    except ValueError as exc:
        return json_error(str(exc))

    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings, spending, events = _user_dataset(store, user_id)
    insights = build_profile_insights(earnings, spending, events, days=days)
    return jsonify(insights)


@app.get("/api/timeline/<int:user_id>")
def get_timeline(user_id):
    try:
        history_days = parse_int(request.args.get("days", 30), "days")
        forecast_days_n = parse_int(request.args.get("forecast", 14), "forecast")
    except ValueError as exc:
        return json_error(str(exc))

    scenario = request.args.get("scenario", "baseline")

    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings, spending, events = _user_dataset(store, user_id)
    insights = build_profile_insights(earnings, spending, events, days=history_days)

    starting_savings = user.get("current_savings", 0)
    forecast_payload = forecast_days(
        insights,
        spending,
        days_ahead=forecast_days_n,
        scenario=scenario,
        starting_savings=starting_savings,
    )

    history_days_payload = []
    running = starting_savings - sum(d.get("net", 0) for d in insights.get("daily", []))
    for d in insights.get("daily", []):
        running += d.get("net", 0)
        history_days_payload.append({
            "date": d["date"],
            "dow": d["dow"],
            "earnings": d["earnings"],
            "spending": d["spending"],
            "net": d["net"],
            "spending_breakdown": d.get("spending_by_category", {}),
            "savings_after": running,
            "is_forecast": False,
        })

    forecast_days_payload = [
        {**fd, "is_forecast": True, "spending_breakdown": fd.get("spending_breakdown", {})}
        for fd in forecast_payload["days"]
    ]

    return jsonify({
        "user_id": user_id,
        "history_days": history_days_payload,
        "forecast_days": forecast_days_payload,
        "scenario": scenario,
        "ending_savings": forecast_payload["ending_savings"],
        "predicted_net": forecast_payload["predicted_net"],
        "days_to_30d_buffer": forecast_payload["days_to_30d_buffer"],
        "target_buffer": forecast_payload["target_buffer"],
        "starting_savings": starting_savings,
        "earnings_summary": insights.get("earnings", {}),
        "spending_summary": insights.get("spending", {}),
    })


@app.get("/api/forecast/<int:user_id>")
def get_forecast(user_id):
    try:
        days_ahead = parse_int(request.args.get("days", 30), "days")
    except ValueError as exc:
        return json_error(str(exc))
    scenario = request.args.get("scenario", "baseline")

    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings, spending, events = _user_dataset(store, user_id)
    insights = build_profile_insights(earnings, spending, events, days=30)

    payload = forecast_days(
        insights,
        spending,
        days_ahead=days_ahead,
        scenario=scenario,
        starting_savings=user.get("current_savings", 0),
    )
    return jsonify(payload)


@app.get("/api/nudges/<int:user_id>")
def get_nudges(user_id):
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    language = normalize_language(
        request.args.get("language"),
        normalize_language(user.get("language"), "hindi"),
    )

    earnings, spending, events = _user_dataset(store, user_id)
    insights = build_profile_insights(earnings, spending, events, days=30)

    earnings_values = [item["amount"] for item in sorted(
        earnings, key=lambda item: item["date"], reverse=True
    )[:30]]
    daily_mandatory = user["mandatory_spend"] / 7
    safety = check_safety_status(user.get("current_savings", 0), daily_mandatory)

    matched_schemes = match_schemes({
        "annual_income": user.get("annual_income", 0),
        "age": user.get("age", 0),
    })

    payload = build_nudges(insights, safety_status=safety, matched_schemes=matched_schemes, language=language)
    return jsonify(payload)


@app.get("/api/crisis/<int:user_id>")
def get_crisis(user_id):
    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    earnings, spending, events = _user_dataset(store, user_id)
    insights = build_profile_insights(earnings, spending, events, days=30)

    daily_mandatory = user["mandatory_spend"] / 7
    safety = check_safety_status(user.get("current_savings", 0), daily_mandatory)
    payload = assess_crisis(
        insights,
        safety,
        user.get("current_savings", 0),
        user.get("mandatory_spend", 0) * 4.33,  # weekly → monthly
    )
    return jsonify(payload)


@app.post("/api/purchase/simulate")
def simulate_purchase():
    data = get_json()
    if data is None:
        return json_error("json_required")

    required = ["user_id", "amount"]
    missing = require_fields(data, required)
    if missing:
        return json_error("missing_fields: {0}".format(",".join(missing)))

    try:
        user_id = parse_int(data["user_id"], "user_id")
        amount = parse_int(data["amount"], "amount")
    except ValueError as exc:
        return json_error(str(exc))

    store = read_store()
    user = find_user(store, user_id)
    if not user:
        return json_error("user_not_found", 404)

    language = normalize_language(data.get("language"), normalize_language(user.get("language"), "hindi"))

    earnings, spending, events = _user_dataset(store, user_id)
    insights = build_profile_insights(earnings, spending, events, days=30)

    daily_mandatory = user["mandatory_spend"] / 7
    current_savings = user.get("current_savings", 0)
    current_days_safe = current_savings / daily_mandatory if daily_mandatory else 0
    new_days_safe = (current_savings - amount) / daily_mandatory if daily_mandatory else 0

    runway = forecast_with_purchase(
        insights,
        spending,
        purchase_amount=amount,
        starting_savings=current_savings,
        days_ahead=30,
        scenario="baseline",
    )

    avg_daily_earnings = insights.get("earnings", {}).get("avg_daily", 0) or 1

    # Use baseline forecast to compute realistic daily savings rate
    base_30d = forecast_days(
        insights,
        spending,
        days_ahead=30,
        scenario="baseline",
        starting_savings=current_savings,
    )
    daily_save_rate = base_30d["predicted_net"] / max(base_30d["days_ahead"], 1)

    options = []
    if daily_save_rate > 0:
        days_to_save = int(round(amount / daily_save_rate))
        save_summary = "About {days} days at your current ~Rs {rate}/day net savings.".format(
            days=days_to_save, rate=int(daily_save_rate)
        )
    else:
        days_to_save = None
        save_summary = (
            "Your current pace doesn't leave room to save for this — consider a loan or work pattern change."
        )

    options.append({
        "id": "save_then_buy",
        "label": "Save first, buy later",
        "summary": save_summary,
        "monthly_emi": 0,
        "tenure_months": 0,
        "total_cost": amount,
        "safety_after_days": round(current_days_safe, 1),
        "recommended": False,
        "days_to_save": days_to_save,
    })

    eligible_loans = match_loans(
        {"annual_income": user.get("annual_income", 0)}, amount=amount
    )
    cheapest_apy = None
    for loan in sorted(eligible_loans, key=lambda l: l.get("apy", 999))[:2]:
        apy = loan.get("apy", 0)
        if cheapest_apy is None:
            cheapest_apy = apy
        tenure = 24
        monthly_rate = apy / 100 / 12
        if monthly_rate > 0:
            emi = amount * monthly_rate * (1 + monthly_rate) ** tenure / ((1 + monthly_rate) ** tenure - 1)
        else:
            emi = amount / tenure
        total_cost = int(emi * tenure)
        options.append({
            "id": "loan_{0}".format(loan["name"].lower().replace(" ", "_")),
            "label": "{0} loan @ {1}% APY".format(loan["name"], apy),
            "summary": "EMI Rs {emi}/month for {tenure} months. Total Rs {total}.".format(
                emi=int(emi), tenure=tenure, total=total_cost
            ),
            "monthly_emi": int(emi),
            "tenure_months": tenure,
            "total_cost": total_cost,
            "safety_after_days": round(current_days_safe, 1),
            "recommended": False,
        })

    options.append({
        "id": "buy_now",
        "label": "Buy now from savings",
        "summary": "Drops your safety from {0:.1f} to {1:.1f} days.".format(
            current_days_safe, max(0, new_days_safe)
        ),
        "monthly_emi": 0,
        "tenure_months": 0,
        "total_cost": amount,
        "safety_after_days": round(max(0, new_days_safe), 1),
        "recommended": False,
    })

    # Pick exactly one recommended option using a transparent rule:
    #   1. If we can save in <= 30 days, that's the cheapest path (no debt).
    #   2. Else if a loan with APY <= 24% is available, recommend it.
    #   3. Else if we can eventually save (any positive rate), recommend save first.
    #   4. Else recommend the lowest-APY loan if any.
    if days_to_save is not None and days_to_save <= 30:
        options[0]["recommended"] = True
    elif cheapest_apy is not None and cheapest_apy <= 24:
        for opt in options:
            if opt["id"].startswith("loan_") and opt["label"].endswith("{0}% APY".format(cheapest_apy)):
                opt["recommended"] = True
                break
    elif days_to_save is not None:
        options[0]["recommended"] = True
    elif cheapest_apy is not None:
        for opt in options:
            if opt["id"].startswith("loan_") and opt["label"].endswith("{0}% APY".format(cheapest_apy)):
                opt["recommended"] = True
                break

    prompt = (
        "You are a financial copilot for an Indian gig worker. "
        "Explain a purchase decision in {language}. Use the native script.\n\n"
        "Purchase: Rs {amount}\n"
        "Current safety: {curr} days. After buying from savings: {after} days.\n"
        "Average daily earnings: Rs {avg_e}. Daily mandatory spend: Rs {avg_s}.\n"
        "30-day predicted ending savings without purchase: Rs {wo}\n"
        "30-day predicted ending savings with purchase: Rs {w}\n\n"
        "Respond in 2-3 sentences. Be specific, no English filler if Hindi/Kannada."
    ).format(
        language=language,
        amount=amount,
        curr=round(current_days_safe, 1),
        after=round(max(0, new_days_safe), 1),
        avg_e=avg_daily_earnings,
        avg_s=int(daily_mandatory),
        wo=runway["without_purchase"]["ending_savings"],
        w=runway["with_purchase"]["ending_savings"],
    )

    explanation = generate_text(prompt)

    return jsonify({
        "purchase_amount": amount,
        "current_safety_days": round(current_days_safe, 1),
        "new_safety_days": round(max(0, new_days_safe), 1),
        "explanation": explanation,
        "language": language,
        "options": options,
        "runway": runway,
    })


if __name__ == "__main__":
    import os as _os
    port = int(_os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
