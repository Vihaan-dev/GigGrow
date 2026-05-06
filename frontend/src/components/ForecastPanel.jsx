import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import BacktestStat from "./BacktestStat";

const SCENARIOS = [
  { id: "pessimistic", label: "Pessimistic", desc: "If days run cool" },
  { id: "baseline", label: "Baseline", desc: "Repeats your normal pattern" },
  { id: "optimistic", label: "Optimistic", desc: "If days run hot" }
];

function formatINR(n) {
  if (n === null || n === undefined) return "-";
  return `₹${Number(n).toLocaleString("en-IN")}`;
}

export default function ForecastPanel({ userId }) {
  const [scenario, setScenario] = useState("baseline");
  const [days, setDays] = useState(30);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!userId) return;
    setLoading(true);
    api
      .getForecast(userId, days, scenario)
      .then((r) => {
        if (!cancelled) setForecast(r);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId, scenario, days]);

  const series = useMemo(() => {
    if (!forecast) return null;
    const W = 360;
    const H = 140;
    const padL = 36;
    const padR = 8;
    const padT = 8;
    const padB = 22;
    const innerW = W - padL - padR;
    const innerH = H - padT - padB;

    const pts = forecast.days || [];
    if (!pts.length) return null;
    const values = pts.map((p) => p.savings_after);
    const lows = pts.map((p) => p.earnings_low_band);
    const highs = pts.map((p) => p.earnings_high_band);

    const minV = Math.min(...values, forecast.starting_savings, 0);
    const maxV = Math.max(...values, forecast.starting_savings, forecast.target_buffer || 0);

    const yFor = (v) => padT + innerH - ((v - minV) / Math.max(maxV - minV, 1)) * innerH;
    const xFor = (i) => padL + (i / Math.max(pts.length - 1, 1)) * innerW;

    const path = values.map((v, i) => `${i === 0 ? "M" : "L"} ${xFor(i)} ${yFor(v)}`).join(" ");
    const targetY = forecast.target_buffer ? yFor(forecast.target_buffer) : null;

    return { W, H, padL, padT, padB, padR, innerW, innerH, pts, path, yFor, xFor, targetY, minV, maxV };
  }, [forecast]);

  if (!userId) return null;

  return (
    <div>
      <div className="scenario-toggle">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            className={`scen-btn ${scenario === s.id ? "active" : ""}`}
            onClick={() => setScenario(s.id)}
            type="button"
          >
            <strong>{s.label}</strong>
            <span>{s.desc}</span>
          </button>
        ))}
      </div>

      {loading && <div className="footer-note">forecasting…</div>}

      {forecast && (
        <>
          <div className="forecast-stats">
            <div>
              <span className="label">Predicted month-end savings</span>
              <strong>{formatINR(forecast.ending_savings)}</strong>
            </div>
            <div>
              <span className="label">Predicted net (next {forecast.days_ahead}d)</span>
              <strong style={{ color: forecast.predicted_net >= 0 ? "var(--accent-2)" : "var(--danger)" }}>
                {forecast.predicted_net >= 0 ? "+" : ""}{formatINR(forecast.predicted_net)}
              </strong>
            </div>
            <div>
              <span className="label">Days to 30-day buffer</span>
              <strong>
                {forecast.days_to_30d_buffer === 0
                  ? "Already there ✓"
                  : forecast.days_to_30d_buffer
                  ? `~${forecast.days_to_30d_buffer} days`
                  : "Not on track"}
              </strong>
            </div>
            <div>
              <span className="label">Target buffer</span>
              <strong>{formatINR(forecast.target_buffer)}</strong>
            </div>
          </div>

          {series && (
            <div className="chart">
              <svg viewBox={`0 0 ${series.W} ${series.H}`} role="img" aria-label="Cash runway forecast">
                {series.targetY !== null && (
                  <>
                    <line
                      x1={series.padL}
                      x2={series.W - series.padR}
                      y1={series.targetY}
                      y2={series.targetY}
                      stroke="var(--accent-2)"
                      strokeDasharray="3 3"
                      strokeWidth="1"
                    />
                    <text x={series.W - series.padR - 4} y={series.targetY - 3} textAnchor="end" fontSize="9" fill="var(--accent-2)">
                      30-day target
                    </text>
                  </>
                )}
                <path
                  d={series.path}
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth="2"
                />
                {series.pts.map((p, i) => (
                  <circle
                    key={i}
                    cx={series.xFor(i)}
                    cy={series.yFor(p.savings_after)}
                    r={2}
                    fill="var(--accent)"
                  />
                ))}
              </svg>
            </div>
          )}

          <div className="footer-note">
            Forecast model: day-of-week mean × event multiplier (rain ×0.65 / holiday ×0.55 / surge ×1.40),
            shifted ±1σ for optimistic / pessimistic. Spending uses category daily baselines plus
            scheduled monthly hits (rent, transfer).
          </div>

          <div style={{ marginTop: 16 }}>
            <BacktestStat userId={userId} />
          </div>
        </>
      )}
    </div>
  );
}
