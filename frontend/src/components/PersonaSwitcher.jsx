import React, { useEffect, useState } from "react";
import { api } from "../api";

const ICON = {
  swiggy: "🛵",
  zomato: "🛵",
  rapido: "🛺",
  upwork: "✍️",
  fiverr: "✍️"
};

export default function PersonaSwitcher({ activeUserId, onSwitch }) {
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .listUsers()
      .then((r) => {
        if (!cancelled) setUsers(r?.users || []);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const active = users.find((u) => u.id === activeUserId);

  if (!users.length) return null;

  return (
    <div className="persona-switcher">
      <button
        type="button"
        className="persona-current ghost"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="persona-icon">{active ? ICON[active.platform] || "👤" : "👤"}</span>
        <span className="persona-meta">
          <strong>{active?.name || `UID ${activeUserId}`}</strong>
          <small>{active?.occupation || active?.platform || ""}</small>
        </span>
        <span className="caret">▾</span>
      </button>

      {open && (
        <div className="persona-menu" role="listbox">
          {users.map((u) => (
            <button
              key={u.id}
              type="button"
              role="option"
              aria-selected={u.id === activeUserId}
              className={`persona-row ${u.id === activeUserId ? "selected" : ""}`}
              onClick={() => {
                setOpen(false);
                onSwitch(u.id);
              }}
            >
              <span className="persona-icon">{ICON[u.platform] || "👤"}</span>
              <span className="persona-meta">
                <strong>{u.name}</strong>
                <small>
                  {u.occupation || u.platform} · {u.city || "—"}
                </small>
                <em>{u.goal}</em>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
