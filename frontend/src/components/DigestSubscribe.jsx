import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function DigestSubscribe({ userId }) {
  const [phone, setPhone] = useState("");
  const [digest, setDigest] = useState(null);
  const [subscribed, setSubscribed] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    setLoading(true);
    api
      .getDigest(userId)
      .then((r) => {
        if (cancelled) return;
        setDigest(r);
        if (r?.subscription) {
          setSubscribed(r.subscription);
          setPhone(r.subscription.phone || "");
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const submit = async (event) => {
    event.preventDefault();
    if (!userId || !phone.trim()) return;
    setStatus("");
    try {
      const r = await api.subscribeDigest({ user_id: userId, phone: phone.trim() });
      setSubscribed(r);
      setStatus("Subscribed. (Demo mode — no real message sent.)");
    } catch (err) {
      setStatus(err.message || "Failed to subscribe.");
    }
  };

  return (
    <div className="digest-wrap">
      <div className="digest-preview">
        <div className="digest-head">
          <strong>Sample weekly digest</strong>
          <span className="chip">WhatsApp · Sundays 10:00 IST</span>
        </div>
        {loading && <div className="footer-note">Composing your digest…</div>}
        {digest && (
          <pre className="digest-body">{digest.preview}</pre>
        )}
        <div className="footer-note">
          Generated from your last 7 days. Phrased by Gemini, grounded in your data — no
          numbers are invented.
        </div>
      </div>

      <form onSubmit={submit} className="digest-form">
        <label className="footer-note">
          Subscribe to the weekly digest:
        </label>
        <div className="form-row">
          <input
            type="tel"
            placeholder="+91 9XXXXXXXXX"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button type="submit" disabled={!phone.trim()}>
            {subscribed ? "Update" : "Subscribe"}
          </button>
        </div>
        {subscribed && (
          <div className="digest-confirm">
            <span className="chip chip-accent">subscribed</span>
            <span>
              {subscribed.phone} · {subscribed.schedule}
            </span>
          </div>
        )}
        {status && <div className="footer-note">{status}</div>}
      </form>
    </div>
  );
}
