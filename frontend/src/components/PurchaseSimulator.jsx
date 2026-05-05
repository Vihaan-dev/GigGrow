import React, { useState } from "react";
import { api } from "../api";

export default function PurchaseSimulator({ userId }) {
  const [amount, setAmount] = useState("");
  const [language, setLanguage] = useState("hindi");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("");

  const simulate = async (event) => {
    event.preventDefault();
    if (!userId || !amount) return;
    setStatus("");
    try {
      const res = await api.simulatePurchase({
        user_id: userId,
        amount,
        language
      });
      setResult(res);
    } catch (err) {
      setStatus(err.message || "Failed to simulate.");
    }
  };

  return (
    <div className="form">
      <div className="form-row">
        <input
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder="Purchase amount"
        />
        <select value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="hindi">Hindi</option>
          <option value="kannada">Kannada</option>
        </select>
      </div>
      <button onClick={simulate}>Simulate</button>
      {result && (
        <div className="list-item">
          <p>Current safety: {result.current_safety_days} days</p>
          <p>After purchase: {result.new_safety_days} days</p>
          <p>{result.explanation}</p>
        </div>
      )}
      {status && <div className="footer-note">{status}</div>}
    </div>
  );
}
