import React, { useState } from "react";
import { api } from "../api";

const today = () => new Date().toISOString().slice(0, 10);

export default function ManualSpendingForm({ userId, onSaved }) {
  const [form, setForm] = useState({
    date: today(),
    amount: "",
    category: "fuel",
    notes: ""
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
      await api.logSpending({
        user_id: userId,
        date: form.date,
        amount: form.amount,
        category: form.category,
        notes: form.notes
      });
      setStatus("Saved.");
      setForm((prev) => ({ ...prev, amount: "", notes: "" }));
      onSaved?.();
    } catch (err) {
      setStatus(err.message || "Failed to save.");
    }
  };

  return (
    <form className="form" onSubmit={submit}>
      <h3>Manual spending</h3>
      <div className="form-row">
        <input type="date" name="date" value={form.date} onChange={onChange} />
        <input name="amount" value={form.amount} onChange={onChange} placeholder="Amount" />
      </div>
      <div className="form-row">
        <select name="category" value={form.category} onChange={onChange}>
          <option value="fuel">Fuel</option>
          <option value="food">Food</option>
          <option value="rent">Rent</option>
          <option value="transfer">Transfer</option>
          <option value="other">Other</option>
        </select>
        <input name="notes" value={form.notes} onChange={onChange} placeholder="Notes" />
      </div>
      <button type="submit">Add spending</button>
      {status && <div className="footer-note">{status}</div>}
    </form>
  );
}
