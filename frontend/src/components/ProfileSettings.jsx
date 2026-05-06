import React, { useEffect, useState } from "react";
import { api } from "../api";

const FIELDS = [
  {
    key: "mandatory_spend",
    label: "Mandatory monthly spend (₹)",
    hint: "Rent, utilities, food essentials. Drives 'days safe' calculation.",
    type: "number",
    min: 0,
    section: "spend"
  },
  {
    key: "household_obligation",
    label: "Money sent home (₹/month)",
    hint: "Counted into your mandatory burn — affects forecasts.",
    type: "number",
    min: 0,
    section: "spend"
  },
  {
    key: "current_savings",
    label: "Current savings (₹)",
    hint: "Real bank/cash balance. Anchors the runway forecast.",
    type: "number",
    min: 0,
    section: "spend"
  },
  {
    key: "annual_income",
    label: "Annual income estimate (₹)",
    hint: "Used for scheme + loan eligibility checks.",
    type: "number",
    min: 0,
    section: "income"
  },
  {
    key: "age",
    label: "Age",
    hint: "PMSBY 18-70, PMJJBY 18-55.",
    type: "number",
    min: 0,
    max: 120,
    section: "income"
  },
  {
    key: "moneylender_debt",
    label: "Moneylender debt outstanding (₹)",
    hint: "Used to compute interest avoided in the GigShield plan.",
    type: "number",
    min: 0,
    section: "debt"
  },
  {
    key: "moneylender_apy",
    label: "Moneylender APY (%)",
    hint: "Annual interest rate on the informal loan. 60 = 5%/month.",
    type: "number",
    min: 0,
    max: 100,
    section: "debt"
  },
  {
    key: "goal",
    label: "Goal",
    hint: "Short description of what you're saving for.",
    type: "text",
    section: "profile"
  }
];

const SECTIONS = [
  { id: "spend", title: "Spending floors" },
  { id: "income", title: "Income & age" },
  { id: "debt", title: "Informal debt (optional)" },
  { id: "profile", title: "Profile" }
];

function asString(v) {
  if (v === null || v === undefined) return "";
  return String(v);
}

export default function ProfileSettings({ userId, onSaved }) {
  const [user, setUser] = useState(null);
  const [draft, setDraft] = useState({});
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!userId) return;
    api
      .getState(userId)
      .then((r) => {
        if (cancelled) return;
        setUser(r.user);
        const initial = {};
        FIELDS.forEach((f) => {
          initial[f.key] = asString(r.user?.[f.key]);
        });
        setDraft(initial);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!user) return <div className="footer-note">Loading account…</div>;

  const change = (key) => (e) => {
    setStatus("");
    setDraft((d) => ({ ...d, [key]: e.target.value }));
  };

  const dirtyFields = FIELDS.filter(
    (f) => asString(user[f.key]) !== draft[f.key]
  );

  const reset = () => {
    const initial = {};
    FIELDS.forEach((f) => {
      initial[f.key] = asString(user?.[f.key]);
    });
    setDraft(initial);
    setStatus("");
  };

  const save = async () => {
    if (dirtyFields.length === 0) return;
    setSaving(true);
    setStatus("");
    const payload = {};
    for (const f of dirtyFields) {
      const raw = draft[f.key];
      payload[f.key] = f.type === "number" ? Number(raw) : raw;
    }
    try {
      const r = await api.updateUser(userId, payload);
      setUser(r.user);
      setStatus(`Saved: ${r.updated_fields.join(", ")}.`);
      if (onSaved) onSaved(r.user);
    } catch (err) {
      setStatus(err.message || "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  // Live previews for the most impactful number — days safe.
  const newDailyMandatory = Number(draft.mandatory_spend || 0) / 7;
  const newSavings = Number(draft.current_savings || 0);
  const newDaysSafe =
    newDailyMandatory > 0 ? (newSavings / newDailyMandatory).toFixed(1) : "—";
  const oldDailyMandatory = Number(user.mandatory_spend || 0) / 7;
  const oldDaysSafe =
    oldDailyMandatory > 0
      ? (Number(user.current_savings || 0) / oldDailyMandatory).toFixed(1)
      : "—";

  return (
    <div className="settings-panel">
      <div className="settings-head">
        <strong>Account settings</strong>
        <span className="footer-note">
          Edit any field below. The dashboard recomputes immediately on save.
        </span>
      </div>

      {SECTIONS.map((sec) => {
        const fields = FIELDS.filter((f) => f.section === sec.id);
        return (
          <div className="settings-section" key={sec.id}>
            <h4 className="sub-title">{sec.title}</h4>
            <div className="settings-grid">
              {fields.map((f) => {
                const dirty = asString(user[f.key]) !== draft[f.key];
                return (
                  <label key={f.key} className={`settings-field ${dirty ? "dirty" : ""}`}>
                    <span className="settings-label">{f.label}</span>
                    <input
                      type={f.type}
                      value={draft[f.key] ?? ""}
                      onChange={change(f.key)}
                      min={f.min}
                      max={f.max}
                    />
                    <span className="settings-hint">{f.hint}</span>
                  </label>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="settings-preview">
        <div>
          <span className="label">Days safe — current</span>
          <strong>{oldDaysSafe}</strong>
        </div>
        <div>
          <span className="label">Days safe — after save</span>
          <strong className={Number(newDaysSafe) >= Number(oldDaysSafe) ? "delta-pos" : "delta-neg"}>
            {newDaysSafe}
          </strong>
        </div>
        <div>
          <span className="label">Pending changes</span>
          <strong>{dirtyFields.length === 0 ? "none" : dirtyFields.length}</strong>
        </div>
      </div>

      <div className="settings-actions">
        <button type="button" className="ghost" onClick={reset} disabled={dirtyFields.length === 0 || saving}>
          Reset
        </button>
        <button type="button" onClick={save} disabled={dirtyFields.length === 0 || saving}>
          {saving ? "Saving…" : `Save${dirtyFields.length ? ` (${dirtyFields.length})` : ""}`}
        </button>
      </div>

      {status && <div className="footer-note">{status}</div>}
    </div>
  );
}
