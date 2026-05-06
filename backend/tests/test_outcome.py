from services.profile_insights import build_profile_insights
from services.outcome import project_outcome
from services.schemes import match_schemes
from services.loans import match_loans


def _matched_for(user):
    schemes = match_schemes({"annual_income": user["annual_income"], "age": user["age"]})
    loans = match_loans({"annual_income": user["annual_income"]}, amount=user.get("moneylender_debt"))
    return schemes, loans


def test_outcome_savings_delta_positive_when_actions_available(thirty_day_dataset, ramesh_user):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    schemes, loans = _matched_for(ramesh_user)
    out = project_outcome(insights, ds["spending"], ramesh_user, loans, schemes, horizon_days=90)
    # GigShield path should not be worse than current path on savings
    assert out["delta"]["savings"] >= 0


def test_outcome_refinance_drops_interest(thirty_day_dataset, ramesh_user):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    schemes, loans = _matched_for(ramesh_user)
    out = project_outcome(insights, ds["spending"], ramesh_user, loans, schemes, horizon_days=90)
    assert out["delta"]["interest_avoided"] > 0  # Ramesh has 60% APY → cheaper loan available
    assert out["gigshield_path"]["interest_paid"] < out["current_path"]["interest_paid"]


def test_outcome_zero_debt_user_has_zero_interest(thirty_day_dataset):
    ds = thirty_day_dataset
    user = {
        "id": 99, "name": "NoDebt", "language": "english", "platform": "swiggy",
        "mandatory_spend": 12000, "household_obligation": 0,
        "current_savings": 20000, "age": 30, "annual_income": 300000,
        "moneylender_debt": 0, "moneylender_apy": 0,
    }
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    schemes, loans = _matched_for(user)
    out = project_outcome(insights, ds["spending"], user, loans, schemes, horizon_days=90)
    assert out["current_path"]["interest_paid"] == 0
    assert out["gigshield_path"]["interest_paid"] == 0


def test_outcome_uses_declared_mandatory_for_days_safe(thirty_day_dataset, ramesh_user):
    ds = thirty_day_dataset
    insights = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    schemes, loans = _matched_for(ramesh_user)
    out = project_outcome(insights, ds["spending"], ramesh_user, loans, schemes, horizon_days=90)
    # days_safe should be on a sane scale: 90-day savings divided by ~1714/day mandatory
    # If we accidentally divided by observed spending, we'd get values in the hundreds.
    assert 5 < out["current_path"]["days_safe_end"] < 200
