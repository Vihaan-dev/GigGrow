import React, { useEffect, useLayoutEffect, useState } from "react";

const STEPS = [
  {
    target: null,
    title: "Welcome to GigShield 👋",
    body: (
      <>
        <p>
          GigShield is a financial copilot for India's gig workers. We track your earnings,
          parse your spending from SMS, calculate a personalised safety buffer, and surface
          schemes you qualify for — in your language.
        </p>
        <p>
          This is a 60-second tour. You can replay it any time from the header.
        </p>
      </>
    )
  },
  {
    target: '[data-tour="briefing"]',
    title: "1 · AI briefing",
    body: (
      <>
        <p>
          Every dashboard load, an AI reads your last 30 days of data and writes a 4-sentence
          briefing in your language. <strong>Every number cited is from your actual data</strong> —
          we reject the briefing if it invents anything.
        </p>
        <p className="footer-note">Click "Show source data" inside the briefing to see exactly what the model saw.</p>
      </>
    )
  },
  {
    target: '[data-tour="kpi"]',
    title: "2 · Your snapshot",
    body: (
      <>
        <p>
          Four numbers that matter: <em>Days safe</em> (how long your savings cover mandatory
          spend), <em>Net</em> (last 30 days), <em>Pace</em> (% toward this month's target),
          and <em>Predicted month-end</em> (forecasted savings).
        </p>
      </>
    )
  },
  {
    target: '[data-tour="nudges"]',
    title: "3 · Smart nudges",
    body: (
      <>
        <p>
          Proactive warnings and opportunities. Each nudge fires from a specific rule on your
          data — click <em>"Why am I seeing this?"</em> on any card to see the trigger formula
          and the source endpoint.
        </p>
      </>
    )
  },
  {
    target: '[data-tour="outcome"]',
    title: "4 · 90-day outcome",
    body: (
      <>
        <p>
          The headline: <em>Current trajectory</em> vs <em>GigShield plan</em> over 90 days.
          The plan applies four levers: cap the worst overspend, lean into your best day,
          refinance high-APY debt, enrol in cheap schemes.
        </p>
        <p className="footer-note">Math is deterministic. The decision is always yours.</p>
      </>
    )
  },
  {
    target: '[data-tour="timeline"]',
    title: "5 · Daily timeline",
    body: (
      <>
        <p>
          30 days of history + 14 days of forecast. Green bars are earnings, red bars are
          spending, the line is your running savings. Forecast region is shaded with a dashed divider.
        </p>
        <p>
          <strong>Click any history day</strong> for an AI explanation citing day-of-week
          expectation and any events on that day (rain, surge, holiday).
        </p>
      </>
    )
  },
  {
    target: '[data-tour="forecast"]',
    title: "6 · Forecast + backtest",
    body: (
      <>
        <p>
          Toggle <em>optimistic / baseline / pessimistic</em> scenarios. The backtest panel
          shows the model's actual accuracy on your held-out last 7 days — MAE, R², 1σ
          coverage. We're honest when the model fits poorly.
        </p>
      </>
    )
  },
  {
    target: '[data-tour="schemes"]',
    title: "7 · Schemes & loans",
    body: (
      <>
        <p>
          PM-KISAN, PMSBY, PMJJBY, microfinance options. We check your profile and show only
          what you qualify for, with the official application link. <strong>No referral
          commissions, ever.</strong>
        </p>
      </>
    )
  },
  {
    target: '[data-tour="privacy"]',
    title: "8 · Your data, your control",
    body: (
      <>
        <p>
          Download everything we know about you as JSON. Or wipe it permanently. Raw SMS text
          is parsed in memory and never persisted — only structured fields (amount, category,
          merchant) are stored.
        </p>
      </>
    )
  },
  {
    target: '[data-tour="chat"]',
    title: "9 · Tool-use chat (top nav)",
    body: (
      <>
        <p>
          The chat tab uses a 2-pass loop: an LLM picks which backend tools to call
          (<code>get_safety_status</code>, <code>simulate_purchase</code>, etc.), the backend
          runs them on real data, then the LLM composes the answer. Tool calls are visible
          before each response.
        </p>
        <p className="footer-note">Voice input works in Hindi, Kannada, English (Chrome/Edge).</p>
      </>
    )
  },
  {
    target: null,
    title: "That's the tour",
    body: (
      <>
        <p>You can switch personas (Ramesh / Lakshmi / Vikram) from the header — each has a different
        financial story so you can see the system generalise.</p>
        <p className="footer-note">Replay this tour any time from the "Tour" button in the header.</p>
      </>
    )
  }
];


function spotlightRect(selector) {
  // Returns VIEWPORT-relative coordinates. Both the spotlight (position:
  // absolute inside our fixed-inset-0 overlay) and the tooltip (position:
  // fixed) interpret their top/left in viewport space, so this is the
  // correct frame of reference.
  if (!selector) return null;
  const el = document.querySelector(selector);
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  return {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
    bottom: rect.bottom,
  };
}

function placeTooltip(rect) {
  // Returns VIEWPORT-relative coords for a position:fixed tooltip.
  // Always clamped to the viewport so the controls are reachable
  // regardless of the target's size or scroll position.
  const W = 380;
  const H = 260;        // height estimate; real tooltip can be slightly different
  const GAP = 14;       // gap between target and tooltip
  const margin = 16;    // min distance from any viewport edge

  if (!rect) {
    return {
      top: Math.max(margin, (window.innerHeight - H) / 2),
      left: Math.max(margin, (window.innerWidth - W) / 2),
      arrow: "none"
    };
  }

  // rect is already in viewport coords.
  const targetTop = rect.top;
  const targetBottom = rect.bottom;
  const targetCenter = rect.left + rect.width / 2;

  const spaceBelow = window.innerHeight - targetBottom;
  const spaceAbove = targetTop;

  let top, arrow;
  if (spaceBelow >= H + GAP + margin) {
    // Comfortably fits below
    top = targetBottom + GAP;
    arrow = "up";
  } else if (spaceAbove >= H + GAP + margin) {
    // Fits above
    top = targetTop - H - GAP;
    arrow = "down";
  } else {
    // Target taller than (or comparable to) viewport. Pin to whichever side
    // has more room and let the clamp keep us on screen.
    if (spaceBelow >= spaceAbove) {
      top = Math.max(margin, window.innerHeight - H - margin);
      arrow = "none";
    } else {
      top = margin;
      arrow = "none";
    }
  }

  // Final clamp so the tooltip can never escape the viewport.
  top = Math.max(margin, Math.min(top, window.innerHeight - H - margin));

  let left = targetCenter - W / 2;
  left = Math.max(margin, Math.min(left, window.innerWidth - W - margin));
  return { top, left, arrow };
}


function TourInner({ onClose }) {
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState(null);
  const [pos, setPos] = useState({ top: 100, left: 100, arrow: "none" });

  const step = STEPS[index];

  // Position-only update — used on user scroll/resize. Never scrolls the page itself.
  const reposition = () => {
    const r = step?.target ? spotlightRect(step.target) : null;
    setRect(r);
    setPos(placeTooltip(r));
  };

  // On step change (or first mount): scroll target into view ONCE, then place
  // spotlight/tooltip. From here on, only the user controls scroll.
  useLayoutEffect(() => {
    const r = step?.target ? spotlightRect(step.target) : null;
    if (r) {
      // r is in viewport coords; convert to doc coord for scrollTo.
      const desiredDocTop = r.top + window.scrollY - 80;
      window.scrollTo({ top: Math.max(0, desiredDocTop), behavior: "smooth" });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    // After the smooth scroll runs the rect will have moved; recompute
    // a couple of frames later so the spotlight follows it.
    const t1 = setTimeout(reposition, 0);
    const t2 = setTimeout(reposition, 320);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  // On user scroll/resize: just reposition the spotlight + tooltip.
  // Crucially, this never calls window.scrollTo, so the user keeps control.
  useEffect(() => {
    let raf = null;
    const handler = () => {
      if (raf) return;
      raf = window.requestAnimationFrame(() => {
        raf = null;
        reposition();
      });
    };
    window.addEventListener("resize", handler);
    window.addEventListener("scroll", handler, { passive: true });
    return () => {
      window.removeEventListener("resize", handler);
      window.removeEventListener("scroll", handler);
      if (raf) cancelAnimationFrame(raf);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  const next = () => {
    if (index < STEPS.length - 1) setIndex(index + 1);
    else onClose();
  };
  const prev = () => {
    if (index > 0) setIndex(index - 1);
  };

  const PAD = 8;
  const spotlightStyle = rect
    ? {
        top: rect.top - PAD,
        left: rect.left - PAD,
        width: rect.width + PAD * 2,
        height: rect.height + PAD * 2
      }
    : null;

  return (
    <div className="tour-overlay" role="dialog" aria-label="GigShield product tour">
      {/* Four panels around the spotlight to dim everything else.
          When no target, a single full-screen dim.
          All values are clamped to >= 0 so partially-off-screen targets
          don't create negative-sized panels. */}
      {rect ? (
        <>
          <div className="tour-dim" style={{ top: 0, left: 0, right: 0, height: Math.max(0, rect.top - PAD) }} />
          <div className="tour-dim" style={{ top: Math.max(0, rect.top - PAD), left: 0, width: Math.max(0, rect.left - PAD), height: Math.max(0, rect.height + PAD * 2) }} />
          <div className="tour-dim" style={{ top: Math.max(0, rect.top - PAD), left: rect.left + rect.width + PAD, right: 0, height: Math.max(0, rect.height + PAD * 2) }} />
          <div className="tour-dim" style={{ top: Math.max(0, rect.bottom + PAD), left: 0, right: 0, bottom: 0 }} />
          <div className="tour-spotlight" style={spotlightStyle} />
        </>
      ) : (
        <div className="tour-dim tour-dim-full" />
      )}

      <div
        className={`tour-tooltip tour-arrow-${pos.arrow}`}
        style={{ top: pos.top, left: pos.left }}
      >
        <div className="tour-tooltip-head">
          <span className="briefing-tag">Tour · {index + 1} of {STEPS.length}</span>
          <button type="button" className="ghost" onClick={onClose}>Skip</button>
        </div>
        <h3>{step.title}</h3>
        <div className="tour-body">{step.body}</div>
        <div className="tour-progress">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`tour-dot ${i === index ? "active" : ""} ${i < index ? "done" : ""}`}
            />
          ))}
        </div>
        <div className="tour-actions">
          <button type="button" className="ghost" onClick={prev} disabled={index === 0}>
            ← Back
          </button>
          <button type="button" onClick={next}>
            {index === STEPS.length - 1 ? "Got it" : "Next →"}
          </button>
        </div>
      </div>
    </div>
  );
}


export default function Tour({ open, onClose }) {
  // Only mount the inner component when the tour is open. This guarantees
  // a fresh `index = 0` on every reopen and avoids any stale-state flicker.
  if (!open) return null;
  return <TourInner onClose={onClose} />;
}
