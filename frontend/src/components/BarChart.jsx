import React from "react";

export default function BarChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart">No spending data yet.</div>;
  }

  const max = Math.max(...data.map((item) => item.value), 1);

  return (
    <div className="chart">
      {data.map((item) => (
        <div className="bar-row" key={item.label}>
          <div>{item.label}</div>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
          <div>Rs {item.value}</div>
        </div>
      ))}
    </div>
  );
}
