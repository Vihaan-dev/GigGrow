import React, { useState } from "react";
import { api } from "../api";
import ConfidenceCaveat from "./ConfidenceCaveat";

function formatINR(n) {
  if (n === null || n === undefined) return "-";
  return `₹${Number(n).toLocaleString("en-IN")}`;
}

function RunwayChart({ runway }) {
  if (!runway) return null;
  const without = runway.without_purchase?.days || [];
  const withP = runway.with_purchase?.days || [];
  if (!without.length || !withP.length) return null;

  const W = 480;
  const H = 160;
  const padL = 44;
  const padR = 8;
  const padT = 12;
  const padB = 24;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  const allValues = [
    ...without.map((d) => d.savings_after),
    ...withP.map((d) => d.savings_after),
    runway.without_purchase.starting_savings,
    runway.with_purchase.starting_savings
  ];
  const min = Math.min(...allValues, 0);
  const max = Math.max(...allValues, 1);
  const xFor = (i) => padL + (i / Math.max(without.length - 1, 1)) * innerW;
  const yFor = (v) => padT + innerH - ((v - min) / Math.max(max - min, 1)) * innerH;

  const pathFor = (arr) =>
    arr.map((d, i) => `${i === 0 ? "M" : "L"} ${xFor(i)} ${yFor(d.savings_after)}`).join(" ");

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Cash runway with vs without purchase">
        <line
          x1={padL}
          x2={W - padR}
          y1={yFor(0)}
          y2={yFor(0)}
          stroke="var(--line)"
          strokeWidth="1"
        />
        <path d={pathFor(without)} fill="none" stroke="var(--accent-2)" strokeWidth="2" />
        <path
          d={pathFor(withP)}
          fill="none"
          stroke="var(--danger)"
          strokeWidth="2"
          strokeDasharray="4 3"
        />
        <text x={padL} y={padT - 2} fontSize="10" fill="var(--accent-2)">
          — without purchase
        </text>
        <text x={padL + 130} y={padT - 2} fontSize="10" fill="var(--danger)">
          --- with purchase
        </text>
      </svg>
    </div>
  );
}

export default function PurchaseSimulator({ userId, defaultLanguage = "hindi" }) {
  const [amount, setAmount] = useState("22000");
  const [language, setLanguage] = useState(defaultLanguage);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const simulate = async (event) => {
    event?.preventDefault();
    if (!userId || !amount) return;
    setStatus("");
    setLoading(true);
    try {
      const res = await api.simulatePurchase({
        user_id: userId,
        amount: Number(amount),
        language
      });
      setResult(res);
    } catch (err) {
      setStatus(err.message || "Failed to simulate.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form">
      <div className="form-row">
        <input
          type="number"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder="Purchase amount, e.g. 22000"
        />
        <select value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="english">English</option>
          <option value="hindi">हिंदी</option>
          <option value="kannada">ಕನ್ನಡ</option>
        </select>
        <button onClick={simulate} disabled={loading}>
          {loading ? "Planning…" : "Plan this purchase"}
        </button>
      </div>

      {status && <div className="footer-note">{status}</div>}

      {result && (
        <div className="purchase-result">
          <div className="purchase-header">
            <div>
              <span className="label">Current safety</span>
              <strong>{result.current_safety_days} days</strong>
            </div>
            <div>
              <span className="label">After buying from savings</span>
              <strong style={{ color: "var(--danger)" }}>
                {result.new_safety_days} days
              </strong>
            </div>
            <div>
              <span className="label">30d savings without</span>
              <strong>{formatINR(result.runway?.without_purchase?.ending_savings)}</strong>
            </div>
            <div>
              <span className="label">30d savings with</span>
              <strong>{formatINR(result.runway?.with_purchase?.ending_savings)}</strong>
            </div>
          </div>

          <RunwayChart runway={result.runway} />

          <div className="footer-note" style={{ marginTop: 12 }}>
            <strong>{result.explanation}</strong>
          </div>

          <div className="options-list">
            {(result.options || []).map((opt) => (
              <div
                key={opt.id}
                className={`option-card ${opt.recommended ? "recommended" : ""}`}
              >
                <div className="option-head">
                  <strong>{opt.label}</strong>
                  {opt.recommended && <span className="chip chip-accent">recommended</span>}
                </div>
                <p>{opt.summary}</p>
                <div className="option-stats">
                  {opt.monthly_emi > 0 && (
                    <span className="chip">EMI {formatINR(opt.monthly_emi)}/mo</span>
                  )}
                  {opt.tenure_months > 0 && (
                    <span className="chip">{opt.tenure_months} months</span>
                  )}
                  {opt.total_cost > 0 && (
                    <span className="chip">total {formatINR(opt.total_cost)}</span>
                  )}
                  <span className="chip">safety {opt.safety_after_days}d after</span>
                </div>
              </div>
            ))}
          </div>

          <div className="decision-strip">
            <ConfidenceCaveat userId={userId} compact />
            <span className="footer-note">
              GigShield's suggestion. <strong>The decision is yours.</strong> No referral
              commissions on any loan or scheme above.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
