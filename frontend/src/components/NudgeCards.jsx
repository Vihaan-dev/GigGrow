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
        <div key={n.id} className={`nudge-card nudge-${n.severity}`}>
          <div className="nudge-head">
            <span className="nudge-icon">{KIND_ICON[n.kind] || "•"}</span>
            <strong>{n.title}</strong>
          </div>
          <p>{n.message}</p>
          <div className="nudge-foot">
            <span className="chip">grounded in: {Object.keys(n.data || {}).join(", ")}</span>
            {n.action && <button className="ghost">{n.action}</button>}
          </div>
        </div>
      ))}
    </div>
  );
}
