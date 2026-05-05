import React, { useMemo, useState } from "react";

const EVENT_ICONS = {
  weather_rain: "☔",
  rain: "☔",
  holiday: "🎉",
  surge_bonus: "⚡",
  surge: "⚡",
  low_demand: "🥀"
};

const DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function formatINR(n) {
  if (n === null || n === undefined) return "-";
  return `₹${Number(n).toLocaleString("en-IN")}`;
}

function shortDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

export default function DailyTimeline({ history = [], forecast = [], startingSavings = 0 }) {
  const all = useMemo(() => {
    const hist = history.map((d) => ({
      ...d,
      earnings: d.earnings || 0,
      spending: d.spending || 0,
      net: (d.earnings || 0) - (d.spending || 0),
      isForecast: false
    }));
    const fc = forecast.map((d) => ({
      ...d,
      earnings: d.predicted_earnings || 0,
      spending: d.predicted_spending || 0,
      net: (d.predicted_earnings || 0) - (d.predicted_spending || 0),
      isForecast: true
    }));
    return [...hist, ...fc];
  }, [history, forecast]);

  const [hoverIdx, setHoverIdx] = useState(null);

  if (all.length === 0) {
    return <div className="chart">No data yet. Run the simulation to populate days.</div>;
  }

  const W = 980;
  const H = 280;
  const padL = 56;
  const padR = 16;
  const padT = 30;
  const padB = 50;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  const maxBar = Math.max(
    ...all.map((d) => Math.max(d.earnings, d.spending)),
    1
  );

  // Cumulative savings
  let running = startingSavings - history.reduce((s, d) => s + ((d.earnings || 0) - (d.spending || 0)), 0);
  const savingsSeries = all.map((d) => {
    running += d.net;
    return running;
  });
  const maxSavings = Math.max(...savingsSeries, startingSavings, 1);
  const minSavings = Math.min(...savingsSeries, 0);

  const colW = innerW / all.length;
  const barHalfHeight = innerH / 2;
  const zeroY = padT + barHalfHeight;

  const xAt = (i) => padL + i * colW + colW / 2;
  const yEarn = (v) => zeroY - (v / maxBar) * barHalfHeight;
  const yEarnHeight = (v) => (v / maxBar) * barHalfHeight;
  const ySpend = (v) => zeroY;
  const ySpendHeight = (v) => (v / maxBar) * barHalfHeight;

  const yLine = (v) => {
    if (maxSavings === minSavings) return padT + innerH / 2;
    return padT + innerH - ((v - minSavings) / (maxSavings - minSavings)) * innerH;
  };

  const linePoints = savingsSeries
    .map((v, i) => `${xAt(i)},${yLine(v)}`)
    .join(" ");

  const forecastStartIdx = history.length;
  const forecastDivX = forecastStartIdx > 0 && forecastStartIdx < all.length
    ? padL + forecastStartIdx * colW
    : null;

  const tickIndices = [];
  const tickEvery = Math.max(1, Math.floor(all.length / 8));
  for (let i = 0; i < all.length; i += tickEvery) tickIndices.push(i);
  if (tickIndices[tickIndices.length - 1] !== all.length - 1) {
    tickIndices.push(all.length - 1);
  }

  const hovered = hoverIdx !== null ? all[hoverIdx] : null;

  return (
    <div className="timeline-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="timeline-svg"
        role="img"
        aria-label="Daily earnings, spending, and savings runway"
        onMouseLeave={() => setHoverIdx(null)}
      >
        {/* zero line */}
        <line
          x1={padL}
          x2={W - padR}
          y1={zeroY}
          y2={zeroY}
          stroke="var(--line)"
          strokeWidth="1"
        />

        {/* forecast region shading */}
        {forecastDivX !== null && (
          <rect
            x={forecastDivX}
            y={padT}
            width={W - padR - forecastDivX}
            height={innerH}
            fill="rgba(224, 122, 95, 0.04)"
          />
        )}
        {forecastDivX !== null && (
          <line
            x1={forecastDivX}
            x2={forecastDivX}
            y1={padT - 8}
            y2={H - padB + 8}
            stroke="var(--accent)"
            strokeWidth="1"
            strokeDasharray="3 3"
          />
        )}
        {forecastDivX !== null && (
          <text
            x={forecastDivX + 4}
            y={padT - 12}
            fontSize="11"
            fill="var(--accent)"
          >
            forecast →
          </text>
        )}

        {/* bars */}
        {all.map((d, i) => {
          const earnH = yEarnHeight(d.earnings);
          const spendH = ySpendHeight(d.spending);
          const x = padL + i * colW + 1;
          const barW = Math.max(2, colW - 2);
          const isHover = hoverIdx === i;
          const earnFill = d.isForecast ? "rgba(42,157,143,0.45)" : "rgba(42,157,143,0.85)";
          const spendFill = d.isForecast ? "rgba(217,72,65,0.45)" : "rgba(217,72,65,0.85)";
          return (
            <g
              key={d.date || i}
              onMouseEnter={() => setHoverIdx(i)}
              style={{ cursor: "pointer" }}
            >
              {/* invisible hit-target full column for easier hover */}
              <rect x={padL + i * colW} y={padT} width={colW} height={innerH} fill="transparent" />
              {d.earnings > 0 && (
                <rect
                  x={x}
                  y={yEarn(d.earnings)}
                  width={barW}
                  height={earnH}
                  fill={earnFill}
                  stroke={isHover ? "#1c1a16" : "none"}
                />
              )}
              {d.spending > 0 && (
                <rect
                  x={x}
                  y={ySpend(d.spending)}
                  width={barW}
                  height={spendH}
                  fill={spendFill}
                  stroke={isHover ? "#1c1a16" : "none"}
                />
              )}
            </g>
          );
        })}

        {/* savings line */}
        <polyline
          points={linePoints}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2"
        />
        {savingsSeries.map((v, i) => (
          <circle
            key={`pt-${i}`}
            cx={xAt(i)}
            cy={yLine(v)}
            r={hoverIdx === i ? 4 : 2.2}
            fill="var(--accent)"
            stroke="#1c1a16"
            strokeWidth="0.5"
          />
        ))}

        {/* event icons above column */}
        {all.map((d, i) => {
          const evts = d.planned_events || d.events || [];
          if (!evts.length) return null;
          return (
            <text
              key={`ev-${i}`}
              x={xAt(i)}
              y={padT - 16}
              fontSize="12"
              textAnchor="middle"
            >
              {evts.slice(0, 1).map((e) => EVENT_ICONS[e] || "•").join("")}
            </text>
          );
        })}

        {/* x-axis ticks */}
        {tickIndices.map((i) => (
          <text
            key={`tick-${i}`}
            x={xAt(i)}
            y={H - padB + 16}
            fontSize="10"
            fill="var(--muted)"
            textAnchor="middle"
          >
            {shortDate(all[i].date)}
          </text>
        ))}

        {/* y-axis labels */}
        <text x={padL - 8} y={padT + 12} fontSize="10" fill="var(--muted)" textAnchor="end">
          earn ↑
        </text>
        <text x={padL - 8} y={H - padB} fontSize="10" fill="var(--muted)" textAnchor="end">
          spend ↓
        </text>
      </svg>

      <div className="timeline-legend">
        <span className="legend-dot legend-earn" /> Earnings
        <span className="legend-dot legend-spend" /> Spending
        <span className="legend-dot legend-savings" /> Savings runway
        <span className="legend-divider" /> Forecast region (dashed)
      </div>

      <div className="timeline-tooltip">
        {hovered ? (
          <div>
            <div className="t-row">
              <strong>{shortDate(hovered.date)}</strong>{" "}
              <span className="chip">{DOW_LABELS[hovered.dow] || ""}</span>{" "}
              {hovered.isForecast && <span className="chip chip-accent">forecast</span>}
            </div>
            <div className="t-row">
              <span>Earnings</span> <strong>{formatINR(hovered.earnings)}</strong>
            </div>
            <div className="t-row">
              <span>Spending</span> <strong>{formatINR(hovered.spending)}</strong>
            </div>
            <div className="t-row">
              <span>Net</span>{" "}
              <strong style={{ color: hovered.net >= 0 ? "var(--accent-2)" : "var(--danger)" }}>
                {hovered.net >= 0 ? "+" : ""}
                {formatINR(hovered.net)}
              </strong>
            </div>
            {hovered.spending_breakdown && Object.keys(hovered.spending_breakdown).length > 0 && (
              <div className="t-breakdown">
                {Object.entries(hovered.spending_breakdown).map(([cat, val]) => (
                  <span className="chip" key={cat}>
                    {cat} {formatINR(val)}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="footer-note">Hover any day to see details</div>
        )}
      </div>
    </div>
  );
}
