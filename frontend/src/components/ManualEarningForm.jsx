import React, { useState } from "react";
import { api } from "../api";

const today = () => new Date().toISOString().slice(0, 10);

export default function ManualEarningForm({ userId, onSaved }) {
  const [form, setForm] = useState({
    date: today(),
    amount: "",
    deliveries: "",
    platform: "swiggy"
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
      await api.logEarning({
        user_id: userId,
        date: form.date,
        amount: form.amount,
        deliveries: form.deliveries,
        platform: form.platform
      });
      setStatus("Saved.");
      setForm((prev) => ({ ...prev, amount: "", deliveries: "" }));
      onSaved?.();
    } catch (err) {
      setStatus(err.message || "Failed to save.");
    }
  };

  return (
    <form className="form" onSubmit={submit}>
      <h3>Manual earnings</h3>
      <div className="form-row">
        <input type="date" name="date" value={form.date} onChange={onChange} />
        <input name="amount" value={form.amount} onChange={onChange} placeholder="Amount" />
      </div>
      <div className="form-row">
        <input
          name="deliveries"
          value={form.deliveries}
          onChange={onChange}
          placeholder="Deliveries"
        />
        <select name="platform" value={form.platform} onChange={onChange}>
          <option value="swiggy">Swiggy</option>
          <option value="zomato">Zomato</option>
        </select>
      </div>
      <button type="submit">Add earnings</button>
      {status && <div className="footer-note">{status}</div>}
    </form>
  );
}
