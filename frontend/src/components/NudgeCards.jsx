import React, { useEffect, useState } from "react";
import { api } from "../api";

const KIND_ICON = {
  overspend: "💸",
  earnings_dip: "📉",
  safety_low: "⚠️",
  safety_warn: "⚠️",
  scheme_opportunity: "🎁",
  opportunity: "📈"
};

const KIND_FORMULA = {
  overspend:
    "trigger when last_7d daily_avg(category) ≥ 1.25 × baseline_daily(category) (excluding rent/transfer)",
  earnings_dip:
    "trigger when (mean(last_7d) − mean(prior_7d)) / mean(prior_7d) ≤ −0.20",
  safety_low:
    "trigger when current_savings / (mandatory_spend / 7) < 3 days",
  safety_warn:
    "trigger when current_savings / (mandatory_spend / 7) < 7 days",
  scheme_opportunity:
    "trigger when matched scheme has annual_cost ≤ ₹50",
  opportunity:
    "trigger when avg(best_dow) ≥ 1.15 × avg_daily_earnings"
};

const KIND_SOURCE = {
  overspend: "GET /api/insights/<uid> (last 30 days)",
  earnings_dip: "GET /api/insights/<uid> (trend_7v7)",
  safety_low: "GET /api/safety/<uid>",
  safety_warn: "GET /api/safety/<uid>",
  scheme_opportunity: "POST /api/schemes/match",
  opportunity: "GET /api/insights/<uid> (dow_pattern)"
};

function NudgeCard({ nudge }) {
  const [why, setWhy] = useState(false);

  return (
    <div className={`nudge-card nudge-${nudge.severity}`}>
      <div className="nudge-head">
        <span className="nudge-icon">{KIND_ICON[nudge.kind] || "•"}</span>
        <strong>{nudge.title}</strong>
      </div>
      <p>{nudge.message}</p>
      <div className="nudge-foot">
        <button
          type="button"
          className="ghost"
          onClick={() => setWhy((v) => !v)}
        >
          {why ? "Hide" : "Why am I seeing this?"}
        </button>
        {nudge.action && <span className="chip">action: {nudge.action}</span>}
      </div>
      {why && (
        <div className="nudge-why">
          <div className="nudge-why-row">
            <span className="label">Trigger rule</span>
            <code>{KIND_FORMULA[nudge.kind] || "(rule undocumented)"}</code>
          </div>
          <div className="nudge-why-row">
            <span className="label">Data the rule used</span>
            <pre>{JSON.stringify(nudge.data || {}, null, 2)}</pre>
          </div>
          <div className="nudge-why-row">
            <span className="label">Source endpoint</span>
            <code>{KIND_SOURCE[nudge.kind] || "(unknown)"}</code>
          </div>
          <div className="footer-note">
            GigShield's recommendation. The decision is yours — ignore, snooze, or act.
          </div>
        </div>
      )}
    </div>
  );
}

export default function NudgeCards({ userId, language }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!userId) return;
    setLoading(true);
    api
      .getNudges(userId, language)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch(() => {
        if (!cancelled) setData({ nudges: [], triggers: [] });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId, language]);

  if (!userId) return null;

  const items = data?.nudges || [];

  if (loading && items.length === 0) {
    return <div className="nudge-row"><div className="footer-note">analysing your week…</div></div>;
  }

  if (!items.length && data) {
    return (
      <div className="nudge-row">
        <div className="nudge-card nudge-info">
          <div className="nudge-head">
            <span className="nudge-icon">✨</span>
            <strong>You're on track</strong>
          </div>
          <p>No urgent nudges right now. Keep going.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="nudge-row">
      {items.map((n) => (
        <NudgeCard key={n.id} nudge={n} />
      ))}
    </div>
  );
}
