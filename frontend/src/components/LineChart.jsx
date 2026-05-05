import React from "react";

export default function LineChart({ data, labels }) {
  if (!data || data.length === 0) {
    return <div className="chart">No data yet.</div>;
  }

  const width = 320;
  const height = 140;
  const padding = 16;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = Math.max(max - min, 1);

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1 || 1)) * (width - padding * 2);
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Earnings trend">
        <polyline
          fill="none"
          stroke="#e07a5f"
          strokeWidth="2"
          points={points.join(" ")}
        />
        {points.map((point, index) => (
          <circle
            key={labels?.[index] || index}
            cx={point.split(",")[0]}
            cy={point.split(",")[1]}
            r="2.5"
            fill="#1c1a16"
          />
        ))}
      </svg>
    </div>
  );
}
