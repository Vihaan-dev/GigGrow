import React, { useEffect, useState } from "react";
import { api } from "../api";

function tier(maePct) {
  if (maePct == null) return null;
  if (maePct < 15) return { label: "high confidence", tone: "positive", note: "Forecast is well-fitted to your pattern." };
  if (maePct < 25) return { label: "fair confidence", tone: "warning", note: "Treat the forecast as directional, not exact." };
  return { label: "low confidence — rough estimate", tone: "danger", note: "Your earning pattern doesn't fit a simple day-of-week model. Use these numbers as rough only." };
}

export default function ConfidenceCaveat({ userId, compact = false }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    api
      .getBacktest(userId, 7)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!data || data.error) return null;
  const m = data.metrics || {};
  const t = tier(m.mae_pct_of_mean);
  if (!t) return null;

  if (compact) {
    return (
      <span className={`chip chip-${t.tone}`}>
        Forecast: {t.label} (MAE {m.mae_pct_of_mean}%)
      </span>
    );
  }

  return (
    <div className={`confidence-caveat conf-${t.tone}`}>
      <div className="conf-head">
        <strong>Forecast {t.label}</strong>
        <span className="footer-note">
          MAE {m.mae_pct_of_mean}% of mean · 1σ coverage {m.band_coverage_pct}% · R² {m.r2 ?? "—"}
        </span>
      </div>
      <p className="footer-note">{t.note}</p>
    </div>
  );
}
