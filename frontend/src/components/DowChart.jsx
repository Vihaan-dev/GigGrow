import React from "react";

const ORDER = [0, 1, 2, 3, 4, 5, 6];

export default function DowChart({ pattern = {}, overallAvg = 0 }) {
  const entries = ORDER.map((dow) => pattern[dow] || { name: "", avg: 0, samples: 0 });
  const max = Math.max(...entries.map((e) => e.avg), overallAvg, 1);

  const W = 320;
  const H = 160;
  const padT = 18;
  const padB = 28;
  const padL = 28;
  const padR = 8;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;
  const colW = innerW / entries.length;
  const yFor = (v) => padT + innerH - (v / max) * innerH;

  const avgY = yFor(overallAvg);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} className="dow-svg" role="img" aria-label="Earnings by day of week">
        {entries.map((e, i) => {
          const x = padL + i * colW + 4;
          const w = colW - 8;
          const y = yFor(e.avg);
          const h = padT + innerH - y;
          const above = e.avg >= overallAvg;
          return (
            <g key={i}>
              <rect
                x={x}
                y={y}
                width={w}
                height={Math.max(h, 1)}
                fill={above ? "var(--accent-2)" : "var(--accent)"}
                opacity={e.samples ? 1 : 0.3}
              />
              <text
                x={x + w / 2}
                y={H - padB + 14}
                fontSize="11"
                textAnchor="middle"
                fill="var(--muted)"
              >
                {e.name}
              </text>
              <text
                x={x + w / 2}
                y={y - 4}
                fontSize="10"
                textAnchor="middle"
                fill="var(--ink)"
              >
                {e.avg ? `₹${e.avg}` : ""}
              </text>
            </g>
          );
        })}
        {overallAvg > 0 && (
          <>
            <line
              x1={padL}
              x2={W - padR}
              y1={avgY}
              y2={avgY}
              stroke="var(--ink)"
              strokeDasharray="3 3"
              strokeWidth="1"
            />
            <text x={padL + 4} y={avgY - 3} fontSize="10" fill="var(--ink)">
              avg ₹{overallAvg}
            </text>
          </>
        )}
      </svg>
    </div>
  );
}
