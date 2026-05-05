import React from "react";

export default function SafetyMeter({ daysSafe }) {
  const safeValue = Number(daysSafe || 0);
  const ratio = Math.min(safeValue / 30, 1);

  return (
    <div className="meter">
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${ratio * 100}%` }} />
      </div>
      <div className="meter-labels">
        <span>0 days</span>
        <span>7 days</span>
        <span>30 days</span>
      </div>
    </div>
  );
}
