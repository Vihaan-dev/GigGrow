import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function SchemeList({ userId }) {
  const [schemes, setSchemes] = useState([]);
  const [status, setStatus] = useState("");

  const load = async () => {
    if (!userId) return;
    setStatus("");
    try {
      const res = await api.matchSchemes({ user_id: userId });
      setSchemes(res.schemes || []);
    } catch (err) {
      setStatus(err.message || "Failed to load schemes.");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  return (
    <div className="list">
      {schemes.map((scheme) => (
        <div className="list-item" key={scheme.name}>
          <h4>{scheme.name}</h4>
          <p>{scheme.description}</p>
          <p>Coverage: Rs {scheme.annual_amount}</p>
          <p>Annual cost: Rs {scheme.annual_cost}</p>
          <p>{scheme.action}</p>
        </div>
      ))}
      {!schemes.length && <div className="footer-note">No schemes yet.</div>}
      {status && <div className="footer-note">{status}</div>}
      <button className="ghost" onClick={load}>Refresh schemes</button>
    </div>
  );
}
