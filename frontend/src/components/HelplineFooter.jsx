import React, { useState } from "react";

const HELPLINES = [
  {
    name: "iCall (TISS)",
    type: "psychosocial counselling",
    phone: "+91 9152987821",
    hours: "Mon-Sat 8am-10pm IST",
    url: "https://icallhelpline.org",
    languages: "English, Hindi, Marathi, Kannada"
  },
  {
    name: "Snehi",
    type: "emotional support",
    phone: "+91 9582208181",
    hours: "10am-6pm IST",
    url: "https://snehi.org",
    languages: "English, Hindi"
  },
  {
    name: "RBI CMS",
    type: "predatory lending grievance",
    phone: "14448",
    hours: "Mon-Fri 9:30am-5:15pm IST",
    url: "https://cms.rbi.org.in",
    languages: "English, Hindi"
  },
  {
    name: "MoneyLife Foundation",
    type: "financial counselling (free)",
    phone: "+91 9869913444",
    hours: "Mon-Fri 10am-6pm IST",
    url: "https://www.moneylife.in/foundation",
    languages: "English, Hindi"
  }
];

export default function HelplineFooter() {
  const [open, setOpen] = useState(false);

  return (
    <footer className="helpline-footer">
      <div className="helpline-footer-row">
        <span className="footer-note">
          GigShield is informational. It does not give regulated financial advice. Decisions are yours.
        </span>
        <button
          type="button"
          className="ghost"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Hide helplines" : "Need to talk to someone? Free helplines"}
        </button>
      </div>
      {open && (
        <div className="helpline-footer-list">
          {HELPLINES.map((h) => (
            <div className="helpline" key={h.name}>
              <div className="helpline-head">
                <strong>{h.name}</strong>
                <span className="chip">{h.type}</span>
              </div>
              <div className="helpline-body">
                <a href={`tel:${h.phone.replace(/\s+/g, "")}`}>{h.phone}</a>
                <span>{h.hours}</span>
                <span>{h.languages}</span>
                <a href={h.url} target="_blank" rel="noreferrer">{h.url}</a>
              </div>
            </div>
          ))}
          <p className="footer-note">
            These are independent NGO helplines. GigShield does not contact anyone on your behalf
            and does not earn referral commissions.
          </p>
        </div>
      )}
    </footer>
  );
}
