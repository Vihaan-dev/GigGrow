import React, { useState } from "react";
import { api } from "../api";

const STORED = [
  { kind: "Account", detail: "Name, language, occupation, city, mandatory monthly spend, current savings, age, annual income" },
  { kind: "Earnings", detail: "Date, amount, deliveries count, platform — never the raw SMS" },
  { kind: "Spending", detail: "Date, amount, category, source (sms/manual), merchant if extracted — never the raw SMS" },
  { kind: "Events", detail: "Type (rain/holiday/surge/etc), redacted summary (≤80 chars), parsed merchant/confidence" }
];

const NEVER_STORED = [
  "Raw SMS message text — parsed in memory and discarded",
  "Phone numbers, account digits, OTPs — redacted to '###' before storage",
  "Location data, device identifiers, contact list",
  "Loan referral commissions or platform partnership flags"
];

export default function PrivacyPanel({ userId, onForgot }) {
  const [showStored, setShowStored] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [hard, setHard] = useState(false);
  const [status, setStatus] = useState("");
  const [working, setWorking] = useState(false);

  const download = async () => {
    if (!userId) return;
    setStatus("");
    setWorking(true);
    try {
      const data = await api.exportUser(userId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `gigshield-export-uid${userId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setStatus("Downloaded.");
    } catch (err) {
      setStatus(err.message || "Export failed.");
    } finally {
      setWorking(false);
    }
  };

  const forget = async () => {
    if (!userId) return;
    if (confirmText !== "I confirm") {
      setStatus('Type exactly: I confirm');
      return;
    }
    setStatus("");
    setWorking(true);
    try {
      const r = await api.forgetUser(userId, { confirm: confirmText, hard });
      setStatus(r.message || "Done.");
      setConfirming(false);
      setConfirmText("");
      if (onForgot) onForgot(r);
    } catch (err) {
      setStatus(err.message || "Forget failed.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <div className="privacy-panel">
      <div className="privacy-head">
        <strong>Your data, your control</strong>
        <span className="footer-note">
          Everything we know about you, downloadable. Wipe-able. No questions asked.
        </span>
      </div>

      <div className="privacy-actions">
        <button type="button" className="ghost" onClick={download} disabled={working}>
          ⬇ Download my data (JSON)
        </button>
        <button
          type="button"
          className="ghost privacy-danger"
          onClick={() => setConfirming((v) => !v)}
          disabled={working}
        >
          {confirming ? "Cancel" : "Delete all my data"}
        </button>
        <button
          type="button"
          className="ghost"
          onClick={() => setShowStored((v) => !v)}
        >
          {showStored ? "Hide" : "What we store / never store"}
        </button>
      </div>

      {confirming && (
        <div className="privacy-confirm">
          <p>
            This will permanently delete your earnings, spending, and events. The model will
            forget you. There is no undo.
          </p>
          <label className="footer-note">
            <input
              type="checkbox"
              checked={hard}
              onChange={(e) => setHard(e.target.checked)}
            />{" "}
            Also delete my user account (you'll need to create a new one to log back in)
          </label>
          <div className="form-row">
            <input
              placeholder='Type "I confirm" to proceed'
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
            />
            <button
              type="button"
              className="privacy-danger"
              onClick={forget}
              disabled={confirmText !== "I confirm" || working}
            >
              Delete now
            </button>
          </div>
        </div>
      )}

      {showStored && (
        <div className="privacy-lists">
          <div>
            <h4 className="sub-title">What we store</h4>
            <ul>
              {STORED.map((s) => (
                <li key={s.kind}>
                  <strong>{s.kind}</strong> — {s.detail}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="sub-title">What we never store</h4>
            <ul>
              {NEVER_STORED.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {status && <div className="footer-note">{status}</div>}
    </div>
  );
}
