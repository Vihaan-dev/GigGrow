import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function LlmStatusBadge() {
  const [status, setStatus] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .getLlmStatus()
      .then((r) => {
        if (!cancelled) setStatus(r);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status) return null;

  const tone = status.ok ? "positive" : status.configured ? "danger" : "muted";
  const label = status.ok
    ? `LLM live · ${status.model}`
    : status.configured
    ? "LLM error — heuristic fallback"
    : "LLM off — heuristic fallback";

  return (
    <div className="llm-status">
      <button
        type="button"
        className={`chip chip-${tone}`}
        onClick={() => setOpen((v) => !v)}
        title="Click for details"
      >
        ● {label}
      </button>
      {open && (
        <div className="llm-status-panel">
          <div className="llm-status-row">
            <span className="label">Configured</span>
            <strong>{status.configured ? "yes" : "no"}</strong>
          </div>
          <div className="llm-status-row">
            <span className="label">Reachable</span>
            <strong>{status.ok ? "yes" : "no"}</strong>
          </div>
          <div className="llm-status-row">
            <span className="label">Model</span>
            <strong>{status.model}</strong>
          </div>
          {status.sample_response && (
            <div className="llm-status-row">
              <span className="label">Sample</span>
              <strong>{status.sample_response}</strong>
            </div>
          )}
          {status.reason && (
            <div className="llm-status-row">
              <span className="label">Reason</span>
              <strong>{status.reason}</strong>
            </div>
          )}
          {status.last_error?.type && (
            <div className="llm-status-row">
              <span className="label">Last error</span>
              <strong>
                {status.last_error.type}: {status.last_error.message}
              </strong>
            </div>
          )}
          {!status.configured && (
            <p className="footer-note">
              Set <code>GEMINI_API_KEY</code> in <code>backend/.env</code> and
              restart the backend. The deterministic heuristic fallback will
              still produce sensible answers in the meantime.
            </p>
          )}
          {status.configured && !status.ok && (
            <p className="footer-note">
              Key is set but the call failed. Check stderr of the backend
              process for the full traceback. Common causes: bad key, region
              block, quota exhausted, deprecated model name.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
