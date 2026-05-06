import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function CrisisBanner({ userId }) {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!userId) return;
    api
      .getCrisis(userId)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!data || !data.triggered) return null;

  return (
    <div className="crisis-banner">
      <div className="crisis-head">
        <strong>⚠ Cash flow looks stressed</strong>
        <span>{data.message}</span>
        <button className="ghost" onClick={() => setOpen((v) => !v)}>
          {open ? "Hide helplines" : "Show free helplines"}
        </button>
      </div>
      <div className="crisis-reasons">
        {data.reasons.map((r) => (
          <span className="chip chip-danger" key={r.code}>{r.detail}</span>
        ))}
      </div>
      {open && (
        <div className="crisis-helplines">
          {data.helplines.map((h) => (
            <div className="helpline" key={h.name}>
              <div className="helpline-head">
                <strong>{h.name}</strong>
                <span className="chip">{h.type}</span>
              </div>
              <div className="helpline-body">
                <a href={`tel:${h.phone.replace(/\s+/g, "")}`}>{h.phone}</a>
                <span>{h.hours}</span>
                <a href={h.url} target="_blank" rel="noreferrer">{h.url}</a>
              </div>
            </div>
          ))}
          <p className="footer-note">
            These are independent NGO helplines. GigShield does not contact anyone on your behalf.
          </p>
        </div>
      )}
    </div>
  );
}
