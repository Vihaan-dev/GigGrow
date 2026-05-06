import React from "react";

function formatINR(n) {
  return `₹${Number(n || 0).toLocaleString("en-IN")}`;
}

export default function VolatilityChip({ avg, std, cv, trend }) {
  const trendArrow = trend > 0.05 ? "↑" : trend < -0.05 ? "↓" : "→";
  const trendPct = Math.round((trend || 0) * 100);
  const cvLabel = cv < 0.15 ? "stable" : cv < 0.3 ? "moderate" : "highly volatile";

  return (
    <div className="vol-chip">
      <div className="vol-row">
        <span className="label">Daily earnings</span>
        <strong>{formatINR(avg)}</strong>
      </div>
      <div className="vol-row">
        <span className="label">Range (±1σ)</span>
        <strong>
          {formatINR(Math.max(0, avg - std))}–{formatINR(avg + std)}
        </strong>
      </div>
      <div className="vol-row">
        <span className="label">Volatility</span>
        <strong>
          CV {cv} <span className="chip">{cvLabel}</span>
        </strong>
      </div>
      <div className="vol-row">
        <span className="label">7d vs prior 7d</span>
        <strong style={{ color: trend > 0 ? "var(--accent-2)" : trend < 0 ? "var(--danger)" : "var(--ink)" }}>
          {trendArrow} {Math.abs(trendPct)}%
        </strong>
      </div>
    </div>
  );
}
