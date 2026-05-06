from services.crisis import assess_crisis


def test_crisis_not_triggered_for_healthy_user():
    insights = {
        "earnings": {"avg_daily": 1500},
        "spending": {"avg_daily": 800},
        "streaks": {"current_low": 0},
    }
    safety = {"days_safe": 12.0}
    out = assess_crisis(insights, safety, current_savings=20000, mandatory_spend_monthly=12000)
    assert out["triggered"] is False
    assert out["score"] == 0


def test_crisis_triggers_on_low_safety_and_overspend():
    insights = {
        "earnings": {"avg_daily": 800},
        "spending": {"avg_daily": 1200},
        "streaks": {"current_low": 5},
    }
    safety = {"days_safe": 1.5}
    out = assess_crisis(insights, safety, current_savings=2000, mandatory_spend_monthly=12000)
    assert out["triggered"] is True
    assert out["score"] >= 2
    assert len(out["helplines"]) >= 1


def test_crisis_helplines_only_when_triggered():
    insights = {"earnings": {"avg_daily": 1500}, "spending": {"avg_daily": 700}, "streaks": {"current_low": 0}}
    safety = {"days_safe": 15}
    out = assess_crisis(insights, safety, current_savings=20000, mandatory_spend_monthly=10000)
    assert out["helplines"] == []
