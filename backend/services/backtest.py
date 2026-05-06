"""Hold-out backtest for the day-of-week earnings forecaster.

We cannot claim a forecaster works without measuring it. This module:
  1. splits the user's history at a chosen point (default: last 7 days held out)
  2. builds the DOW pattern from the train portion only
  3. predicts each test day using the same model the live system uses
     (DOW mean, with rain/holiday/surge multipliers from observed events)
  4. reports MAE, MAPE, R², and 1-sigma band coverage

Output is intentionally simple — judges should be able to read four
numbers and immediately understand whether the model is honest.
"""

import math
import statistics
from collections import defaultdict
from datetime import date, datetime

from .forecast import EVENT_MULTIPLIERS


def _parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _aggregate_by_date(items):
    by_date = defaultdict(int)
    for item in items:
        by_date[item["date"]] += item.get("amount", 0) or 0
    return by_date


def _events_by_date(events):
    by_date = defaultdict(list)
    for evt in events:
        by_date[evt["date"]].append(evt.get("type"))
    return by_date


def run_backtest(earnings, events, *, holdout_days=7):
    """Return a backtest report against the last `holdout_days` of history."""
    earnings_by_date = _aggregate_by_date(earnings)
    events_by_date = _events_by_date(events)

    if len(earnings_by_date) < holdout_days + 7:
        return {"error": "need_at_least_{0}_days".format(holdout_days + 7)}

    sorted_dates = sorted(earnings_by_date.keys())
    train_dates = sorted_dates[:-holdout_days]
    test_dates = sorted_dates[-holdout_days:]

    # Build DOW pattern from train only
    train_by_dow = defaultdict(list)
    for d in train_dates:
        dow = _parse_date(d).weekday()
        train_by_dow[dow].append(earnings_by_date[d])

    dow_mean = {dow: int(round(statistics.mean(values))) for dow, values in train_by_dow.items() if values}
    dow_std = {
        dow: int(round(statistics.stdev(values))) if len(values) > 1 else 0
        for dow, values in train_by_dow.items()
    }
    train_values = [earnings_by_date[d] for d in train_dates]
    overall_mean = int(round(statistics.mean(train_values))) if train_values else 0
    overall_std = int(round(statistics.stdev(train_values))) if len(train_values) > 1 else 0

    # Predict each test day
    rows = []
    abs_errors = []
    pct_errors = []
    in_band = 0
    sst = 0
    sse = 0
    test_actuals = [earnings_by_date[d] for d in test_dates]
    test_mean = statistics.mean(test_actuals) if test_actuals else 0

    for d in test_dates:
        dow = _parse_date(d).weekday()
        base = dow_mean.get(dow, overall_mean)
        sigma = dow_std.get(dow) or overall_std

        multiplier = 1.0
        applied = []
        for evt_type in events_by_date.get(d, []):
            m = EVENT_MULTIPLIERS.get(evt_type)
            if m is None:
                continue
            multiplier *= m
            applied.append("{0}×{1:.2f}".format(evt_type, m))

        predicted = max(0, int(round(base * multiplier)))
        low_band = max(0, int(round((base - sigma) * multiplier)))
        high_band = max(0, int(round((base + sigma) * multiplier)))

        actual = earnings_by_date[d]
        err = actual - predicted
        abs_errors.append(abs(err))
        if actual > 0:
            pct_errors.append(abs(err) / actual * 100)
        if low_band <= actual <= high_band:
            in_band += 1
        sse += err * err
        sst += (actual - test_mean) ** 2

        rows.append({
            "date": d,
            "dow": dow,
            "predicted": predicted,
            "low_band": low_band,
            "high_band": high_band,
            "actual": actual,
            "abs_error": abs(err),
            "applied_multipliers": applied,
        })

    mae = int(round(statistics.mean(abs_errors))) if abs_errors else 0
    mape = round(statistics.mean(pct_errors), 1) if pct_errors else 0.0
    coverage = round(in_band / len(test_dates) * 100, 1) if test_dates else 0.0
    r2 = round(1 - (sse / sst), 3) if sst > 0 else None
    rmse = int(round(math.sqrt(sse / len(test_dates)))) if test_dates else 0

    return {
        "model": "dow_mean_x_event_multiplier",
        "train_days": len(train_dates),
        "test_days": len(test_dates),
        "metrics": {
            "mae": mae,
            "mae_pct_of_mean": round(mae / test_mean * 100, 1) if test_mean else 0,
            "mape": mape,
            "rmse": rmse,
            "r2": r2,
            "band_coverage_pct": coverage,
            "test_mean_earnings": int(round(test_mean)),
        },
        "rows": rows,
    }
