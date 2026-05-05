import React from "react";

export default function StatCard({ label, value, sublabel, tone = "neutral" }) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {sublabel && <div className="sub">{sublabel}</div>}
    </div>
  );
}
