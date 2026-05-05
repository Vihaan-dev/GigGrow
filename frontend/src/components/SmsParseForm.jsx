import React, { useState } from "react";
import { api } from "../api";

const today = () => new Date().toISOString().slice(0, 10);

export default function SmsParseForm({ userId, onSaved }) {
  const [smsText, setSmsText] = useState("");
  const [status, setStatus] = useState("");
  const [date, setDate] = useState(today());

  const submit = async (event) => {
    event.preventDefault();
    if (!userId) return;
    setStatus("");
    try {
      await api.parseSms({
        user_id: userId,
        sms_text: smsText,
        date
      });
      setStatus("Parsed and saved.");
      setSmsText("");
      onSaved?.();
    } catch (err) {
      setStatus(err.message || "Failed to parse.");
    }
  };

  return (
    <form className="form" onSubmit={submit}>
      <h3>Parse SMS spend</h3>
      <div className="form-row">
        <input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
      </div>
      <textarea
        value={smsText}
        onChange={(event) => setSmsText(event.target.value)}
        placeholder="Paste SMS text"
      />
      <button type="submit">Parse SMS</button>
      {status && <div className="footer-note">{status}</div>}
    </form>
  );
}
