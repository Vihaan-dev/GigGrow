import React, { useEffect, useState } from "react";
import { api } from "./api";

import StatCard from "./components/StatCard";
import ManualEarningForm from "./components/ManualEarningForm";
import ManualSpendingForm from "./components/ManualSpendingForm";
import SmsParseForm from "./components/SmsParseForm";
import EventIngestForm from "./components/EventIngestForm";
import ChatPanel from "./components/ChatPanel";
import SchemeList from "./components/SchemeList";
import LoanList from "./components/LoanList";
import PurchaseSimulator from "./components/PurchaseSimulator";
import DailyTimeline from "./components/DailyTimeline";
import DowChart from "./components/DowChart";
import CategoryDonut from "./components/CategoryDonut";
import ForecastPanel from "./components/ForecastPanel";
import NudgeCards from "./components/NudgeCards";
import CrisisBanner from "./components/CrisisBanner";
import VolatilityChip from "./components/VolatilityChip";
import PersonaSwitcher from "./components/PersonaSwitcher";
import OutcomeCard from "./components/OutcomeCard";
import DigestSubscribe from "./components/DigestSubscribe";
import Briefing from "./components/Briefing";
import PrivacyPanel from "./components/PrivacyPanel";
import HelplineFooter from "./components/HelplineFooter";
import ConfidenceCaveat from "./components/ConfidenceCaveat";
import Tour from "./components/Tour";
import ProfileSettings from "./components/ProfileSettings";

const ROUTES = {
  DASHBOARD: "#/dashboard",
  TIMELINE: "#/timeline",
  PURCHASE: "#/purchase",
  CHAT: "#/chat",
  MANUAL: "#/manual",
  EVENTS: "#/events",
  SCHEMES: "#/schemes"
};

const NAV_ITEMS = [
  { id: "dashboard", route: ROUTES.DASHBOARD, label: "Dashboard" },
  { id: "timeline", route: ROUTES.TIMELINE, label: "Timeline" },
  { id: "purchase", route: ROUTES.PURCHASE, label: "Plan Purchase" },
  { id: "chat", route: ROUTES.CHAT, label: "Chat" },
  { id: "schemes", route: ROUTES.SCHEMES, label: "Schemes & Loans" },
  { id: "manual", route: ROUTES.MANUAL, label: "Manual" },
  { id: "events", route: ROUTES.EVENTS, label: "Events" }
];

const emptyProfile = {
  name: "",
  language: "hindi",
  platform: "swiggy",
  mandatory_spend: "12000",
  household_obligation: "5000",
  current_savings: "13700",
  age: "29",
  annual_income: "300000"
};

function formatINR(value) {
  if (value === null || value === undefined) return "-";
  return `₹${Number(value).toLocaleString("en-IN")}`;
}

function HeaderNav({
  activeRoute,
  activeUserId,
  language,
  onSwitchPersona,
  onLanguageChange,
  onRefresh,
  onLogout,
  onStartTour
}) {
  return (
    <header className="header">
      <div className="header-top">
        <div className="brand">
          <h1>GigShield</h1>
          <span>Daily-resolution finance for India's gig workers.</span>
        </div>
        <div className="user-controls">
          <PersonaSwitcher activeUserId={activeUserId} onSwitch={onSwitchPersona} />
          <select value={language} onChange={(e) => onLanguageChange(e.target.value)}>
            <option value="english">English</option>
            <option value="hindi">हिंदी</option>
            <option value="kannada">ಕನ್ನಡ</option>
          </select>
          <button className="ghost" onClick={onStartTour} title="Replay product tour">
            ✨ Tour
          </button>
          <button className="ghost" onClick={onRefresh}>Refresh</button>
          <button className="ghost" onClick={onLogout}>Logout</button>
        </div>
      </div>
      <nav className="primary-nav" data-tour="nav">
        {NAV_ITEMS.map((item) => (
          <a
            key={item.id}
            href={item.route}
            data-tour={item.id === "chat" ? "chat" : undefined}
            className={`nav-link ${activeRoute === item.route ? "active" : ""}`}
          >
            {item.label}
          </a>
        ))}
      </nav>
    </header>
  );
}

function LoginPage({ profile, onProfileChange, onCreate, onLogin }) {
  const [loginId, setLoginId] = useState("");
  return (
    <div className="login-shell">
      <div className="login-card">
        <h1>GigShield</h1>
        <p className="footer-note">Financial resilience copilot for India's 153M gig workers.</p>
        <div className="login-section">
          <h3>Login with your user id</h3>
          <div className="form-row">
            <input
              placeholder="e.g. 1"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
            />
            <button onClick={() => onLogin(Number(loginId))} disabled={!loginId}>
              Continue
            </button>
          </div>
        </div>
        <div className="divider">or create a new demo</div>
        <div className="login-section">
          <div className="form-row">
            <input
              name="name"
              value={profile.name}
              onChange={onProfileChange}
              placeholder="Name (e.g. Ramesh)"
            />
            <select name="language" value={profile.language} onChange={onProfileChange}>
              <option value="english">English</option>
              <option value="hindi">Hindi</option>
              <option value="kannada">Kannada</option>
            </select>
          </div>
          <div className="form-row">
            <input
              name="mandatory_spend"
              value={profile.mandatory_spend}
              onChange={onProfileChange}
              placeholder="Mandatory monthly spend"
            />
            <input
              name="current_savings"
              value={profile.current_savings}
              onChange={onProfileChange}
              placeholder="Current savings"
            />
          </div>
          <button onClick={onCreate}>Create demo user</button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [loggedUser, setLoggedUser] = useState(() =>
    localStorage.getItem("gigshield_user") || null
  );
  const [route, setRoute] = useState(window.location.hash || ROUTES.DASHBOARD);
  const [language, setLanguage] = useState(
    () => localStorage.getItem("gigshield_lang") || "hindi"
  );
  const [profile, setProfile] = useState(emptyProfile);
  const [state, setState] = useState(null);
  const [insights, setInsights] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [tourOpen, setTourOpen] = useState(false);

  // Auto-show the tour the first time a user lands on the dashboard.
  useEffect(() => {
    if (!loggedUser) return;
    const seen = localStorage.getItem("gigshield_tour_seen");
    if (!seen) {
      // Slight delay so the DOM has the targeted sections rendered
      const t = setTimeout(() => setTourOpen(true), 600);
      return () => clearTimeout(t);
    }
  }, [loggedUser]);

  const startTour = () => setTourOpen(true);
  const finishTour = () => {
    localStorage.setItem("gigshield_tour_seen", "1");
    setTourOpen(false);
  };

  useEffect(() => {
    const onHash = () => setRoute(window.location.hash || ROUTES.DASHBOARD);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const userId = loggedUser ? Number(loggedUser) : null;

  const refresh = async () => {
    if (!userId) return;
    setError("");
    setInfo("");
    try {
      const [stateRes, insightsRes, timelineRes] = await Promise.all([
        api.getState(userId),
        api.getInsights(userId, 30),
        api.getTimeline(userId, 30, 14, "baseline")
      ]);
      setState(stateRes);
      setInsights(insightsRes);
      setTimeline(timelineRes);
    } catch (err) {
      setError(err.message || "Failed to load.");
    }
  };

  useEffect(() => {
    if (userId) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // validate stored user actually exists on the backend
  useEffect(() => {
    if (!userId) return;
    let mounted = true;
    api.getState(userId).catch(() => {
      if (!mounted) return;
      localStorage.removeItem("gigshield_user");
      setLoggedUser(null);
      setInfo("Your session was reset. Please login again.");
    });
    return () => {
      mounted = false;
    };
  }, [userId]);

  const handleProfileChange = (event) => {
    const { name, value } = event.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const createUser = async () => {
    setError("");
    try {
      const created = await api.createUser({
        name: profile.name || "Ramesh",
        language: profile.language,
        platform: profile.platform,
        mandatory_spend: profile.mandatory_spend,
        household_obligation: profile.household_obligation,
        current_savings: profile.current_savings,
        age: profile.age,
        annual_income: profile.annual_income
      });
      localStorage.setItem("gigshield_user", String(created.id));
      setLoggedUser(String(created.id));
    } catch (err) {
      setError(err.message || "Failed to create user.");
    }
  };

  const loginAs = (id) => {
    if (!Number.isInteger(id) || id <= 0) return;
    localStorage.setItem("gigshield_user", String(id));
    setLoggedUser(String(id));
    window.location.hash = ROUTES.DASHBOARD;
  };

  const switchPersona = (id) => {
    if (!Number.isInteger(id) || id <= 0) return;
    if (String(id) === loggedUser) return;
    localStorage.setItem("gigshield_user", String(id));
    setLoggedUser(String(id));
    setState(null);
    setInsights(null);
    setTimeline(null);
    setError("");
    setInfo(`Switched to persona ${id}`);
  };

  const logout = () => {
    localStorage.removeItem("gigshield_user");
    setLoggedUser(null);
    setState(null);
    setInsights(null);
    setTimeline(null);
    window.location.hash = ROUTES.DASHBOARD;
  };

  const changeLanguage = (lang) => {
    setLanguage(lang);
    localStorage.setItem("gigshield_lang", lang);
  };

  const totals = state?.totals || { earnings: 0, spending: 0 };
  const earningsSummary = insights?.earnings || {};
  const spendingSummary = insights?.spending || {};
  const safety = state?.safety || {};
  const projectedNet = timeline?.predicted_net ?? 0;
  const endingSavings = timeline?.ending_savings ?? state?.user?.current_savings ?? 0;

  const monthlyMandatory = state?.user ? Number(state.user.mandatory_spend) : 0;
  const monthlyTarget = monthlyMandatory * 1.25;
  const monthEarnings = totals.earnings;
  const pacePct = monthlyTarget ? Math.min(100, Math.round((monthEarnings / monthlyTarget) * 100)) : 0;

  const safetyTone =
    safety.status === "secure" ? "positive" :
    safety.status === "okay" ? "warning" :
    "danger";

  if (!loggedUser) {
    return (
      <div className="app">
        <LoginPage
          profile={profile}
          onProfileChange={handleProfileChange}
          onCreate={createUser}
          onLogin={loginAs}
        />
        {error && <div className="footer-note error">{error}</div>}
      </div>
    );
  }

  const Dashboard = (
    <>
      <CrisisBanner userId={userId} />

      <Briefing userId={userId} language={language} />

      <section className="hero">
        <div>
          <span className="hello">Welcome back, {state?.user?.name || "—"}</span>
          <h2>{state?.user?.platform || "—"} partner · {state?.user?.language || language}</h2>
        </div>
        <div className="hero-stats">
          <div>
            <span className="label">Today's day-type</span>
            <strong>{(state?.summary?.days || []).slice(-1)[0]?.day_type || "—"}</strong>
          </div>
          <div>
            <span className="label">Avg / day</span>
            <strong>{formatINR(earningsSummary.avg_daily)}</strong>
          </div>
          <div>
            <span className="label">Volatility</span>
            <strong>CV {earningsSummary.cv ?? 0}</strong>
          </div>
        </div>
      </section>

      <section className="section" data-tour="nudges">
        <div className="section-title">
          <h2>Smart nudges</h2>
          <span>Grounded in your last 30 days</span>
        </div>
        <NudgeCards userId={userId} language={language} />
      </section>

      <section className="section" data-tour="kpi">
        <div className="stat-grid">
          <StatCard
            label="Days safe"
            value={safety.days_safe ?? "-"}
            sublabel={safety.status || ""}
            tone={safetyTone}
          />
          <StatCard
            label="Net (last 30d)"
            value={formatINR(totals.earnings - totals.spending)}
            sublabel={`Earned ${formatINR(totals.earnings)} · Spent ${formatINR(totals.spending)}`}
            tone={totals.earnings >= totals.spending ? "positive" : "danger"}
          />
          <StatCard
            label="Pace this month"
            value={`${pacePct}%`}
            sublabel={`Target ${formatINR(monthlyTarget)}`}
            tone={pacePct >= 80 ? "positive" : pacePct >= 50 ? "warning" : "danger"}
          />
          <StatCard
            label="Predicted month-end"
            value={formatINR(endingSavings)}
            sublabel={`Net next 14d: ${projectedNet >= 0 ? "+" : ""}${formatINR(projectedNet)}`}
            tone={projectedNet >= 0 ? "positive" : "danger"}
          />
        </div>
      </section>

      <section className="section section-feature" data-tour="outcome">
        <div className="section-title">
          <h2>90-day outcome</h2>
          <span>Current trajectory vs GigShield plan</span>
        </div>
        <OutcomeCard userId={userId} />
      </section>

      <section className="section" data-tour="timeline">
        <div className="section-title">
          <h2>Daily timeline</h2>
          <span>30 days history + 14 days forecast</span>
        </div>
        {timeline && (
          <DailyTimeline
            history={timeline.history_days}
            forecast={timeline.forecast_days}
            startingSavings={timeline.starting_savings}
            userId={userId}
            language={language}
          />
        )}
      </section>

      <div className="split-2" data-tour="forecast">
        <section className="section">
          <div className="section-title">
            <h2>Profile insights</h2>
            <span>Your patterns</span>
          </div>
          <h4 className="sub-title">Earnings by day of week</h4>
          <DowChart pattern={insights?.dow_pattern} overallAvg={earningsSummary.avg_daily} />
          <div className="footer-note">
            Best: <strong>{insights?.best_day_of_week?.name}</strong> ({formatINR(insights?.best_day_of_week?.avg)}) ·
            Worst: <strong>{insights?.worst_day_of_week?.name}</strong> ({formatINR(insights?.worst_day_of_week?.avg)})
          </div>

          <h4 className="sub-title" style={{ marginTop: 16 }}>Volatility</h4>
          <VolatilityChip
            avg={earningsSummary.avg_daily}
            std={earningsSummary.std_dev}
            cv={earningsSummary.cv}
            trend={earningsSummary.trend_7v7}
          />

          <h4 className="sub-title" style={{ marginTop: 16 }}>Spending mix</h4>
          <CategoryDonut
            mix={spendingSummary.by_category_mix_pct}
            totals={spendingSummary.by_category_total}
          />
        </section>

        <section className="section">
          <div className="section-title">
            <h2>Forecast</h2>
            <span>Where you're headed</span>
          </div>
          <ForecastPanel userId={userId} />
        </section>
      </div>

      <section className="section" data-tour="schemes">
        <div className="section-title">
          <h2>Schemes &amp; loans you qualify for</h2>
          <span>Free safety nets first</span>
        </div>
        <div className="split">
          <SchemeList userId={userId} onRefresh={refresh} />
          <LoanList userId={userId} onRefresh={refresh} />
        </div>
      </section>

      <section className="section">
        <div className="section-title">
          <h2>Weekly WhatsApp digest</h2>
          <span>How GigShield reaches Ramesh, Lakshmi, Vikram</span>
        </div>
        <DigestSubscribe userId={userId} />
      </section>

      <section className="section" data-tour="settings">
        <div className="section-title">
          <h2>Account settings</h2>
          <span>Edit your spend floors, savings, debt — recomputes everything</span>
        </div>
        <ProfileSettings userId={userId} onSaved={refresh} />
      </section>

      <section className="section" data-tour="privacy">
        <div className="section-title">
          <h2>Privacy</h2>
          <span>Your data, your control</span>
        </div>
        <PrivacyPanel userId={userId} onForgot={() => { setState(null); setInsights(null); setTimeline(null); refresh(); }} />
      </section>
    </>
  );

  const Timeline = (
    <section className="section">
      <div className="section-title">
        <h2>Daily timeline (extended)</h2>
        <span>Hover any day for breakdown</span>
      </div>
      {timeline && (
        <DailyTimeline
          history={timeline.history_days}
          forecast={timeline.forecast_days}
          startingSavings={timeline.starting_savings}
        />
      )}
    </section>
  );

  const Purchase = (
    <section className="section">
      <div className="section-title">
        <h2>Plan a purchase</h2>
        <span>See impact on cash runway</span>
      </div>
      <PurchaseSimulator userId={userId} defaultLanguage={language} />
    </section>
  );

  const Chat = (
    <section className="section">
      <div className="section-title">
        <h2>Chat copilot</h2>
        <span>Hindi · Kannada · English (with voice)</span>
      </div>
      <ChatPanel userId={userId} defaultLanguage={language} />
    </section>
  );

  const Manual = (
    <>
      <section className="section">
        <div className="section-title">
          <h2>Log earnings</h2>
          <span>Manual entry</span>
        </div>
        <ManualEarningForm userId={userId} onSaved={refresh} />
      </section>
      <section className="section">
        <div className="section-title">
          <h2>Log spending</h2>
          <span>Manual entry</span>
        </div>
        <ManualSpendingForm userId={userId} onSaved={refresh} />
      </section>
      <section className="section">
        <div className="section-title">
          <h2>Parse SMS</h2>
          <span>Paste a bank SMS</span>
        </div>
        <SmsParseForm userId={userId} onSaved={refresh} />
      </section>
    </>
  );

  const Events = (
    <section className="section">
      <div className="section-title">
        <h2>Ingest event</h2>
        <span>Inject a simulated event</span>
      </div>
      <EventIngestForm userId={userId} onSaved={refresh} />
    </section>
  );

  const Schemes = (
    <section className="section">
      <div className="section-title">
        <h2>Schemes &amp; loans</h2>
        <span>What you qualify for</span>
      </div>
      <div className="split">
        <SchemeList userId={userId} onRefresh={refresh} />
        <LoanList userId={userId} onRefresh={refresh} />
      </div>
    </section>
  );

  return (
    <div className="app">
      <HeaderNav
        activeRoute={route}
        activeUserId={userId}
        language={language}
        onSwitchPersona={switchPersona}
        onLanguageChange={changeLanguage}
        onRefresh={refresh}
        onLogout={logout}
        onStartTour={startTour}
      />
      <Tour open={tourOpen} onClose={finishTour} />
      {error && <div className="footer-note error">{error}</div>}
      {info && <div className="footer-note">{info}</div>}
      <main className="main">
        {route === ROUTES.DASHBOARD && Dashboard}
        {route === ROUTES.TIMELINE && Timeline}
        {route === ROUTES.PURCHASE && Purchase}
        {route === ROUTES.CHAT && Chat}
        {route === ROUTES.MANUAL && Manual}
        {route === ROUTES.EVENTS && Events}
        {route === ROUTES.SCHEMES && Schemes}
      </main>
      <HelplineFooter />
    </div>
  );
}
