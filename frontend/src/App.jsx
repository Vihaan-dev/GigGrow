import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import StatCard from "./components/StatCard";
import LineChart from "./components/LineChart";
import BarChart from "./components/BarChart";
import SafetyMeter from "./components/SafetyMeter";
import NoticeList from "./components/NoticeList";
import ManualEarningForm from "./components/ManualEarningForm";
import ManualSpendingForm from "./components/ManualSpendingForm";
import SmsParseForm from "./components/SmsParseForm";
import EventIngestForm from "./components/EventIngestForm";
import ChatPanel from "./components/ChatPanel";
import SchemeList from "./components/SchemeList";
import LoanList from "./components/LoanList";
import PurchaseSimulator from "./components/PurchaseSimulator";

// Simple hash-based router keys
const ROUTES = {
  DASHBOARD: "#/dashboard",
  MANUAL: "#/manual",
  EVENTS: "#/events",
  CHAT: "#/chat",
  PURCHASE: "#/purchase",
  SCHEMES: "#/schemes",
  PROFILE: "#/profile",
};

import HeaderNav from "./components/HeaderNav";
import LoginPage from "./pages/LoginPage";

const emptyProfile = {
  name: "",
  language: "hindi",
  platform: "swiggy",
  mandatory_spend: "12000",
  household_obligation: "5000",
  current_savings: "3200",
  age: "29",
  annual_income: "300000"
};

function formatCurrency(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `Rs ${Number(value).toLocaleString()}`;
}

export default function App() {
  const [userId, setUserId] = useState("1");
  const [profile, setProfile] = useState(emptyProfile);
  const [state, setState] = useState(null);
  const [earnings, setEarnings] = useState(null);
  const [spending, setSpending] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const userIdNumber = Number(userId);
  const canLoad = Number.isInteger(userIdNumber) && userIdNumber > 0;

  const refreshAll = async () => {
    if (!canLoad) {
      setError("Enter a valid user id.");
      return;
    }
    setLoading(true);
    setError("");
    setInfo("");
    try {
      const [stateRes, earningsRes, spendingRes] = await Promise.all([
        api.getState(userIdNumber),
        api.getEarnings(userIdNumber, 30),
        api.getSpending(userIdNumber, 30)
      ]);
      setState(stateRes);
      setEarnings(earningsRes);
      setSpending(spendingRes);
    } catch (err) {
      setError(err.message || "Failed to load data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canLoad) {
      refreshAll();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const summaryDays = state?.summary?.days || [];
  const lastDay = summaryDays[summaryDays.length - 1];
  const totals = state?.totals || { earnings: 0, spending: 0 };

  const notices = useMemo(() => {
    if (!state) return [];
    const items = [];

    if (state.safety?.status === "at_risk") {
      items.push({
        title: "Safety buffer is low",
        detail: "Current safety is below 7 days. Build a buffer before major spends.",
        tone: "danger"
      });
    }

    if (totals.spending > totals.earnings && totals.earnings > 0) {
      items.push({
        title: "Spending is higher than earnings",
        detail: "Keep expenses below income to avoid shortfalls.",
        tone: "warning"
      });
    }

    if (!summaryDays.length) {
      items.push({
        title: "No activity yet",
        detail: "Add earnings or ingest events to start tracking.",
        tone: "warning"
      });
    }

    return items;
  }, [state, totals, summaryDays]);

  const trendData = summaryDays.map((day) => day.earnings || 0);
  const spendCategories = spending?.by_category || {};
  const spendData = Object.entries(spendCategories).map(([label, value]) => ({
    label,
    value
  }));

  const handleProfileChange = (event) => {
    const { name, value } = event.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const createUser = async () => {
    setError("");
    setInfo("");
    try {
      const payload = {
        name: profile.name || "Ramesh",
        language: profile.language,
        platform: profile.platform,
        mandatory_spend: profile.mandatory_spend,
        household_obligation: profile.household_obligation,
        current_savings: profile.current_savings,
        age: profile.age,
        annual_income: profile.annual_income
      };
      const created = await api.createUser(payload);
      setUserId(String(created.id));
      // set as logged in
      localStorage.setItem("gigshield_user", String(created.id));
      setLoggedUser(String(created.id));
      setInfo(`Created user ${created.id}`);
    } catch (err) {
      setError(err.message || "Failed to create user.");
    }
  };
      // logged user state and basic routing
      const [loggedUser, setLoggedUser] = useState(() => localStorage.getItem("gigshield_user") || null);
      const [route, setRoute] = useState(window.location.hash || ROUTES.DASHBOARD);

      useEffect(() => {
        const onHash = () => setRoute(window.location.hash || ROUTES.DASHBOARD);
        window.addEventListener("hashchange", onHash);
        return () => window.removeEventListener("hashchange", onHash);
      }, []);

      const navigate = (r) => {
        window.location.hash = r;
      };

      const loginAs = (id) => {
        localStorage.setItem("gigshield_user", String(id));
        setLoggedUser(String(id));
        setUserId(String(id));
        navigate(ROUTES.DASHBOARD);
      };

      const logout = () => {
        localStorage.removeItem("gigshield_user");
        setLoggedUser(null);
        setUserId("");
        navigate(ROUTES.DASHBOARD);
      };

      // Simple pages as internal components
      const LoginPage = () => {
        const [loginId, setLoginId] = useState("");
        return (
          <div className="center-card">
            <h2>Welcome to GigShield</h2>
            <p>Please login with your user id or create a new demo user.</p>
            <div className="form-row">
              <input placeholder="Existing user id" value={loginId} onChange={(e) => setLoginId(e.target.value)} />
              <button onClick={() => loginAs(Number(loginId))} disabled={!loginId}>Login</button>
            </div>
            <div className="divider">or</div>
            <div>
              <h3>Create demo user</h3>
              <div className="form-row">
                <input name="name" value={profile.name} onChange={handleProfileChange} placeholder="Name" />
                <select name="language" value={profile.language} onChange={handleProfileChange}>
                  <option value="english">English</option>
                  <option value="hindi">Hindi</option>
                  <option value="kannada">Kannada</option>
                </select>
                <button onClick={createUser}>Create</button>
              </div>
            </div>
          </div>
        );
      };

      const HeaderNav = () => (
        <header className="header">
          <div className="header-top">
            <div className="brand">
              <h1>GigShield</h1>
              <span>Safety and clarity for gig worker finances.</span>
            </div>
            <div className="toolbar">
              <nav className="nav">
                <a href="#/dashboard">Dashboard</a>
                <a href="#/manual">Manual</a>
                <a href="#/events">Events</a>
                <a href="#/chat">Chat</a>
                <a href="#/purchase">Purchase</a>
                <a href="#/schemes">Schemes</a>
              </nav>
              <div className="user-controls">
                <span>UID: {loggedUser}</span>
                <button onClick={() => { refreshAll(); }}>Refresh</button>
                <button onClick={logout}>Logout</button>
              </div>
            </div>
          </div>
        </header>
      );

      const DashboardPage = () => (
        <div className="grid">
          <div>
            <section className="section">
              <div className="section-title"><h2>Snapshot</h2><span>Last 30 days</span></div>
              <div className="stat-grid">
                <StatCard label="Safety days" value={state?.safety?.days_safe ?? "-"} sublabel={state?.safety?.status || ""} tone={state?.safety?.status === "secure" ? "positive" : state?.safety?.status === "okay" ? "warning" : "danger"} />
                <StatCard label="Total earnings" value={formatCurrency(totals.earnings)} sublabel={`Projected month ${formatCurrency(state?.summary?.projected_month_earnings)}`} tone="positive" />
                <StatCard label="Total spending" value={formatCurrency(totals.spending)} sublabel="All categories" tone="warning" />
                <StatCard label="Current day type" value={lastDay?.day_type || "-"} sublabel={lastDay?.date || ""} />
              </div>
              <SafetyMeter daysSafe={state?.safety?.days_safe} />
            </section>

            <section className="section"><div className="section-title"><h2>Earnings trend</h2><span>Daily earnings</span></div><LineChart data={trendData} labels={summaryDays.map((d)=>d.date)} /><div className="footer-note">Projected month earnings uses the last 7 days average.</div></section>

            <section className="section"><div className="section-title"><h2>Spending mix</h2><span>Categories</span></div><BarChart data={spendData} /></section>

            <section className="section"><div className="section-title"><h2>Notices</h2><span>Actions to take</span></div><NoticeList items={notices} /></section>

            <section className="section"><div className="section-title"><h2>Schemes and loans</h2><span>Eligibility</span></div><div className="split"><SchemeList userId={Number(loggedUser)} onRefresh={refreshAll} /><LoanList userId={Number(loggedUser)} onRefresh={refreshAll} /></div></section>
          </div>

          <div>
            <section className="section"><div className="section-title"><h2>Profile</h2><span>Edit</span></div><div className="form"><input name="name" value={profile.name} onChange={handleProfileChange} placeholder="Name" /><button onClick={() => createUser()}>Update</button></div></section>
          </div>
        </div>
      );

      const ManualPage = () => (
        <div className="container">
          <h2>Manual inputs</h2>
          <ManualEarningForm userId={Number(loggedUser)} onSaved={refreshAll} />
          <ManualSpendingForm userId={Number(loggedUser)} onSaved={refreshAll} />
          <SmsParseForm userId={Number(loggedUser)} onSaved={refreshAll} />
        </div>
      );

      const EventsPage = () => (
        <div className="container">
          <h2>Event ingestion</h2>
          <EventIngestForm userId={Number(loggedUser)} onSaved={refreshAll} />
        </div>
      );

      const ChatPage = () => (
        <div className="container"><h2>Chat assistant</h2><ChatPanel userId={Number(loggedUser)} /></div>
      );

      const PurchasePage = () => (
        <div className="container"><h2>Purchase simulator</h2><PurchaseSimulator userId={Number(loggedUser)} /></div>
      );

      const SchemesPage = () => (
        <div className="container"><h2>Schemes & Loans</h2><div className="split"><SchemeList userId={Number(loggedUser)} onRefresh={refreshAll} /><LoanList userId={Number(loggedUser)} onRefresh={refreshAll} /></div></div>
      );

      // validate logged user exists on backend
      useEffect(() => {
        let mounted = true;
        const checkUser = async () => {
          if (!loggedUser) return;
          try {
            await api.getState(Number(loggedUser));
          } catch (err) {
            // clear invalid stored user and force login
            localStorage.removeItem("gigshield_user");
            if (mounted) {
              setLoggedUser(null);
              setUserId("");
              window.location.hash = ROUTES.DASHBOARD;
              setInfo("Your session was reset. Please login again.");
            }
          }
        };
        checkUser();
        return () => { mounted = false; };
      }, [loggedUser]);

      // render
      if (!loggedUser) {
        return <div className="app"><LoginPage profile={profile} handleProfileChange={handleProfileChange} createUser={createUser} loginAs={loginAs} /></div>;
      }

      // show header + page
      return (
        <div className="app">
          <HeaderNav />
          <main className="main">
            {route === ROUTES.DASHBOARD && <DashboardPage />}
            {route === ROUTES.MANUAL && <ManualPage />}
            {route === ROUTES.EVENTS && <EventsPage />}
            {route === ROUTES.CHAT && <ChatPage />}
            {route === ROUTES.PURCHASE && <PurchasePage />}
            {route === ROUTES.SCHEMES && <SchemesPage />}
            {route === ROUTES.PROFILE && <div className="container">Profile page</div>}
          </main>
        </div>
      );
}
