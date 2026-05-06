from services.profile_insights import build_profile_insights


def test_insights_compute_avg_and_volatility(thirty_day_dataset):
    ds = thirty_day_dataset
    out = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    assert out["earnings"]["avg_daily"] > 0
    assert out["earnings"]["std_dev"] > 0
    assert 0 <= out["earnings"]["cv"] <= 5


def test_insights_dow_pattern_marks_weekend_higher(thirty_day_dataset):
    ds = thirty_day_dataset
    out = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    pattern = out["dow_pattern"]
    weekend_avg = (pattern[4]["avg"] + pattern[5]["avg"] + pattern[6]["avg"]) / 3
    weekday_avg = (pattern[0]["avg"] + pattern[1]["avg"]) / 2
    # In our synthetic data weekends pay more
    assert weekend_avg > weekday_avg


def test_insights_best_and_worst_dow_consistent(thirty_day_dataset):
    ds = thirty_day_dataset
    out = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    best = out["best_day_of_week"]
    worst = out["worst_day_of_week"]
    assert best["avg"] >= worst["avg"]


def test_insights_category_baseline_excludes_zero(thirty_day_dataset):
    ds = thirty_day_dataset
    out = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    baseline = out["spending"]["by_category_daily_baseline"]
    # We seeded fuel + rent + transfer
    assert "fuel" in baseline
    assert baseline["fuel"] > 0


def test_insights_daily_array_length(thirty_day_dataset):
    ds = thirty_day_dataset
    out = build_profile_insights(ds["earnings"], ds["spending"], ds["events"], days=30, end_date=ds["end_date"])
    assert len(out["daily"]) == 30
