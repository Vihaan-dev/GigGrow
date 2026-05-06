from services.profile_insights import build_profile_insights
from services.forecast import forecast_days, forecast_with_purchase, EVENT_MULTIPLIERS


def test_forecast_returns_requested_horizon(thirty_day_dataset):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    fc = forecast_days(insights, ds["spending"], days_ahead=14, scenario="baseline", starting_savings=10000)
    assert fc["days_ahead"] == 14
    assert len(fc["days"]) == 14


def test_forecast_optimistic_higher_than_pessimistic(thirty_day_dataset):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    base = forecast_days(insights, ds["spending"], days_ahead=14, scenario="baseline", starting_savings=10000)
    opt = forecast_days(insights, ds["spending"], days_ahead=14, scenario="optimistic", starting_savings=10000)
    pes = forecast_days(insights, ds["spending"], days_ahead=14, scenario="pessimistic", starting_savings=10000)
    assert opt["ending_savings"] >= base["ending_savings"] >= pes["ending_savings"]


def test_forecast_with_purchase_subtracts_amount(thirty_day_dataset):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    runway = forecast_with_purchase(
        insights, ds["spending"],
        purchase_amount=22000, starting_savings=20000, days_ahead=30, scenario="baseline",
    )
    delta = runway["without_purchase"]["ending_savings"] - runway["with_purchase"]["ending_savings"]
    assert delta == 22000  # one-time purchase shifts the curve by exactly its amount


def test_forecast_event_multipliers_known():
    assert EVENT_MULTIPLIERS["weather_rain"] < 1.0
    assert EVENT_MULTIPLIERS["holiday"] < 1.0
    assert EVENT_MULTIPLIERS["surge_bonus"] > 1.0


def test_forecast_planned_event_drops_earnings(thirty_day_dataset):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    base = forecast_days(insights, ds["spending"], days_ahead=14, scenario="baseline", starting_savings=10000)
    rainy = forecast_days(
        insights, ds["spending"],
        days_ahead=14, scenario="baseline", starting_savings=10000,
        planned_events=[{"date": d["date"], "type": "weather_rain"} for d in base["days"]],
    )
    assert rainy["total_predicted_earnings"] < base["total_predicted_earnings"]
