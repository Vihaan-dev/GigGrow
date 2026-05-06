import React, { useEffect, useState } from "react";
import { api } from "../api";
import ConfidenceCaveat from "./ConfidenceCaveat";

function formatINR(n) {
  if (n === null || n === undefined) return "-";
  return `₹${Number(n).toLocaleString("en-IN")}`;
}

function PathColumn({ path, accent }) {
  return (
    <div className={`outcome-col outcome-col-${accent}`}>
      <div className="outcome-label">{path.label}</div>
      <div className="outcome-value">{formatINR(path.ending_savings)}</div>
      <div className="outcome-sub">ending savings · 90 days</div>
      <div className="outcome-stats">
        <div>
          <span className="label">Days safe</span>
          <strong>{path.days_safe_end}</strong>
        </div>
        <div>
          <span className="label">Interest paid</span>
          <strong>{formatINR(path.interest_paid)}</strong>
        </div>
        {path.scheme_coverage_added > 0 && (
          <div>
            <span className="label">Insurance cover</span>
            <strong>{formatINR(path.scheme_coverage_added)}</strong>
          </div>
        )}
      </div>
    </div>
  );
}

export default function OutcomeCard({ userId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    setLoading(true);
    api
      .getOutcome(userId, 90)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!userId) return null;
  if (loading && !data) {
    return <div className="footer-note">Projecting 90-day outcome…</div>;
  }
  if (!data) return null;

  const dPos = (data.delta?.savings ?? 0) >= 0;

  return (
    <div className="outcome-card">
      <div className="outcome-head">
        <div>
          <h3>If you follow the GigShield plan for 90 days</h3>
          <span className="footer-note">
            Compared to your current trajectory · grounded in your last 30 days
          </span>
        </div>
        <div className="outcome-delta">
          <span className="label">Delta</span>
          <strong className={dPos ? "delta-pos" : "delta-neg"}>
            {dPos ? "+" : ""}{formatINR(data.delta?.savings)}
          </strong>
          <small>
            {data.delta?.days_safe >= 0 ? "+" : ""}
            {data.delta?.days_safe} days safe ·{" "}
            {formatINR(data.delta?.interest_avoided)} interest avoided
          </small>
        </div>
      </div>

      <div className="outcome-grid">
        <PathColumn path={data.current_path} accent="current" />
        <PathColumn path={data.gigshield_path} accent="plan" />
      </div>

      {(data.actions || []).length > 0 && (
        <div className="outcome-actions">
          <h4>Actions in the GigShield plan</h4>
          <ol>
            {data.actions.map((a) => (
              <li key={a.code}>
                <strong>{a.title}</strong>
                <span> — {a.detail}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      <ConfidenceCaveat userId={userId} />

      <div className="footer-note">
        The GigShield path applies four levers: cap the worst overspend category,
        capture 25% of the best day-of-week uplift, refinance high-APY debt to the
        cheapest eligible loan, and enrol in low-cost government schemes. Math is
        deterministic from your data. <strong>This is a suggestion, not advice — the
        decision is yours.</strong>
      </div>
    </div>
  );
}
