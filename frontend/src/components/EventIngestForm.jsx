import React, { useState } from "react";
import { api } from "../api";

const today = () => new Date().toISOString().slice(0, 10);

const eventTypes = [
  "sms_expense",
  "sms_income",
  "manual_spend",
  "weather_rain",
  "holiday",
  "surge_bonus",
  "low_demand",
  "loan_query",
  "scheme_query"
];

export default function EventIngestForm({ userId, onSaved }) {
  const [form, setForm] = useState({
    type: "sms_expense",
    date: today(),
    amount: "",
    sms_text: "",
    category: "fuel",
    message: "",
    tags: ""
  });
  const [status, setStatus] = useState("");

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!userId) return;
    setStatus("");
    try {
      const payload = {
        user_id: userId,
        type: form.type,
        date: form.date,
        amount: form.amount || undefined,
        sms_text: form.sms_text || undefined,
        category: form.category || undefined,
        message: form.message || undefined,
        tags: form.tags ? form.tags.split(",").map((t) => t.trim()).filter(Boolean) : []
      };
      await api.ingestEvents(payload);
      setStatus("Event ingested.");
      setForm((prev) => ({ ...prev, amount: "", sms_text: "", message: "" }));
      onSaved?.();
    } catch (err) {
      setStatus(err.message || "Failed to ingest.");
    }
  };

  return (
    <form className="form" onSubmit={submit}>
      <div className="form-row">
        <select name="type" value={form.type} onChange={onChange}>
          {eventTypes.map((type) => (
            <option value={type} key={type}>
              {type}
            </option>
          ))}
        </select>
        <input type="date" name="date" value={form.date} onChange={onChange} />
      </div>
      <div className="form-row">
        <input name="amount" value={form.amount} onChange={onChange} placeholder="Amount" />
        <input name="category" value={form.category} onChange={onChange} placeholder="Category" />
      </div>
      <textarea
        name="sms_text"
        value={form.sms_text}
        onChange={onChange}
        placeholder="SMS text or event message"
      />
      <input
        name="tags"
        value={form.tags}
        onChange={onChange}
        placeholder="Tags (comma separated)"
      />
      <button type="submit">Ingest event</button>
      {status && <div className="footer-note">{status}</div>}
    </form>
  );
}
