import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function LoanList({ userId }) {
  const [loans, setLoans] = useState([]);
  const [status, setStatus] = useState("");

  const load = async () => {
    if (!userId) return;
    setStatus("");
    try {
      const res = await api.matchLoans({ user_id: userId });
      setLoans(res.loans || []);
    } catch (err) {
      setStatus(err.message || "Failed to load loans.");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  return (
    <div className="list">
      {loans.map((loan) => (
        <div className="list-item" key={loan.name}>
          <h4>{loan.name}</h4>
          <p>APY: {loan.apy}%</p>
          <p>Range: Rs {loan.min_amount} - Rs {loan.max_amount}</p>
          <p>Link: {loan.link}</p>
        </div>
      ))}
      {!loans.length && <div className="footer-note">No loans yet.</div>}
      {status && <div className="footer-note">{status}</div>}
      <button className="ghost" onClick={load}>Refresh loans</button>
    </div>
  );
}
