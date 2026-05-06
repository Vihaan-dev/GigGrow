import React from "react";

const PALETTE = [
  "#e07a5f",
  "#2a9d8f",
  "#f2c14e",
  "#5b8def",
  "#a47cb6",
  "#7a8c4e",
  "#b6582e"
];

function polar(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function ringSegmentPath(cx, cy, rOuter, rInner, startA, endA) {
  const startOuter = polar(cx, cy, rOuter, startA);
  const endOuter = polar(cx, cy, rOuter, endA);
  const startInner = polar(cx, cy, rInner, startA);
  const endInner = polar(cx, cy, rInner, endA);
  const large = endA - startA > 180 ? 1 : 0;
  return [
    `M ${startOuter.x} ${startOuter.y}`,
    `A ${rOuter} ${rOuter} 0 ${large} 1 ${endOuter.x} ${endOuter.y}`,
    `L ${endInner.x} ${endInner.y}`,
    `A ${rInner} ${rInner} 0 ${large} 0 ${startInner.x} ${startInner.y}`,
    "Z"
  ].join(" ");
}

export default function CategoryDonut({ mix = {}, totals = {} }) {
  const entries = Object.entries(mix).filter(([, v]) => v > 0);
  if (entries.length === 0) {
    return <div className="chart">No spending yet.</div>;
  }

  const W = 220;
  const H = 220;
  const cx = W / 2;
  const cy = H / 2;
  const rOuter = 90;
  const rInner = 60;

  const total = Object.values(totals).reduce((a, b) => a + b, 0);

  let cursor = 0;
  const segments = entries.map(([cat, pct], i) => {
    const start = cursor;
    const end = cursor + (pct / 100) * 360;
    cursor = end;
    return {
      cat,
      pct,
      d: ringSegmentPath(cx, cy, rOuter, rInner, start, end),
      color: PALETTE[i % PALETTE.length]
    };
  });

  return (
    <div className="donut-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Spending by category">
        {segments.map((s) => (
          <path key={s.cat} d={s.d} fill={s.color} />
        ))}
        <text x={cx} y={cy - 4} fontSize="11" textAnchor="middle" fill="var(--muted)">
          total spend
        </text>
        <text x={cx} y={cy + 14} fontSize="16" textAnchor="middle" fill="var(--ink)" fontWeight="600">
          ₹{total.toLocaleString("en-IN")}
        </text>
      </svg>
      <div className="donut-legend">
        {segments.map((s) => (
          <div key={s.cat} className="donut-row">
            <span className="dot" style={{ background: s.color }} />
            <span className="cat-name">{s.cat}</span>
            <span className="cat-pct">{s.pct}%</span>
            <span className="cat-amt">₹{(totals[s.cat] || 0).toLocaleString("en-IN")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
