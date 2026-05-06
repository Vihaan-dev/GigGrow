from services.backtest import run_backtest


def test_backtest_returns_metrics(thirty_day_dataset):
    ds = thirty_day_dataset
    out = run_backtest(ds["earnings"], ds["events"], holdout_days=7)
    assert "metrics" in out
    m = out["metrics"]
    for key in ("mae", "mape", "rmse", "band_coverage_pct", "test_mean_earnings"):
        assert key in m


def test_backtest_train_test_split(thirty_day_dataset):
    ds = thirty_day_dataset
    out = run_backtest(ds["earnings"], ds["events"], holdout_days=7)
    assert out["train_days"] == len(ds["earnings"]) - 7
    assert out["test_days"] == 7


def test_backtest_returns_per_day_rows(thirty_day_dataset):
    ds = thirty_day_dataset
    out = run_backtest(ds["earnings"], ds["events"], holdout_days=7)
    assert len(out["rows"]) == 7
    for row in out["rows"]:
        assert row["abs_error"] >= 0
        assert row["low_band"] <= row["high_band"]


def test_backtest_short_history_errors():
    short = [{"date": f"2026-04-0{i+1}", "amount": 1000} for i in range(5)]
    out = run_backtest(short, [], holdout_days=7)
    assert "error" in out
