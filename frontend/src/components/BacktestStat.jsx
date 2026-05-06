import React, { useEffect, useState } from "react";
import { api } from "../api";

function formatINR(n) {
  if (n === null || n === undefined) return "-";
  return `₹${Number(n).toLocaleString("en-IN")}`;
}

function quality(maePct) {
  if (maePct == null) return { label: "n/a", tone: "muted" };
  if (maePct < 15) return { label: "strong", tone: "positive" };
  if (maePct < 25) return { label: "fair", tone: "warning" };
  return { label: "poor fit", tone: "danger" };
}

export default function BacktestStat({ userId }) {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    setLoading(true);
    api
      .getBacktest(userId, 7)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch((err) => {
        if (!cancelled) setData({ error: err.message || "request_failed" });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (loading && !data) {
    return <div className="footer-note">Backtesting forecaster…</div>;
  }
  if (!data) return null;
  if (data.error) {
    return (
      <div className="backtest">
        <div className="backtest-head">
          <strong>Forecaster accuracy</strong>
          <span className="chip">backtest unavailable</span>
        </div>
        <div className="footer-note">
          Need at least 14 days of earnings to backtest. {data.error}
        </div>
      </div>
    );
  }

  const m = data.metrics || {};
  const q = quality(m.mae_pct_of_mean);

  return (
    <div className="backtest">
      <div className="backtest-head">
        <strong>Forecaster accuracy</strong>
        <span className={`chip chip-${q.tone}`}>{q.label}</span>
        <span className="footer-note">
          Trained on {data.train_days} days · tested on last {data.test_days} days · holdout
        </span>
      </div>
      <div className="backtest-stats">
        <div>
          <span className="label">MAE</span>
          <strong>{formatINR(m.mae)}</strong>
          <small>{m.mae_pct_of_mean}% of mean</small>
        </div>
        <div>
          <span className="label">MAPE</span>
          <strong>{m.mape}%</strong>
        </div>
        <div>
          <span className="label">R²</span>
          <strong>{m.r2 ?? "—"}</strong>
        </div>
        <div>
          <span className="label">1σ band coverage</span>
          <strong>{m.band_coverage_pct}%</strong>
        </div>
      </div>
      <button type="button" className="ghost" onClick={() => setOpen((v) => !v)}>
        {open ? "Hide per-day predictions" : "Show per-day predictions"}
      </button>
      {open && (
        <table className="backtest-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Predicted</th>
              <th>1σ band</th>
              <th>Actual</th>
              <th>Error</th>
              <th>Multipliers</th>
            </tr>
          </thead>
          <tbody>
            {(data.rows || []).map((r) => {
              const inBand = r.actual >= r.low_band && r.actual <= r.high_band;
              return (
                <tr key={r.date}>
                  <td>{r.date}</td>
                  <td>{formatINR(r.predicted)}</td>
                  <td>
                    {formatINR(r.low_band)}–{formatINR(r.high_band)}
                    {inBand ? " ✓" : ""}
                  </td>
                  <td>{formatINR(r.actual)}</td>
                  <td>{formatINR(r.abs_error)}</td>
                  <td>
                    {(r.applied_multipliers || []).length === 0 ? (
                      <span className="footer-note">none</span>
                    ) : (
                      r.applied_multipliers.join(", ")
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      <div className="footer-note">
        Model: <code>predicted = day_of_week_mean × event_multiplier</code>.
        Coverage = % of test days where actual fell inside the 1σ band.
        Honest reporting includes failures: lumpy or volatile patterns produce
        higher error and lower R² — those users would need a different model class.
      </div>
    </div>
  );
}
