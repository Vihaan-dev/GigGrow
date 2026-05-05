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
      setInfo(`Created user ${created.id}`);
    } catch (err) {
      setError(err.message || "Failed to create user.");
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <div className="brand">
            <h1>GigShield</h1>
            <span>Safety and clarity for gig worker finances.</span>
          </div>
          <div className="toolbar">
            <label>
              User id
              <input
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                placeholder="1"
              />
            </label>
            <button onClick={refreshAll} disabled={loading || !canLoad}>
              {loading ? "Loading" : "Refresh"}
            </button>
            {error && <span className="chip">{error}</span>}
            {info && <span className="chip">{info}</span>}
          </div>
        </div>
      </header>

      <div className="grid">
        <div>
          <section className="section">
            <div className="section-title">
              <h2>Snapshot</h2>
              <span>Last 30 days</span>
            </div>
            <div className="stat-grid">
              <StatCard
                label="Safety days"
                value={state?.safety?.days_safe ?? "-"}
                sublabel={state?.safety?.status || ""}
                tone={state?.safety?.status === "secure" ? "positive" : state?.safety?.status === "okay" ? "warning" : "danger"}
              />
              <StatCard
                label="Total earnings"
                value={formatCurrency(totals.earnings)}
                sublabel={`Projected month ${formatCurrency(state?.summary?.projected_month_earnings)}`}
                tone="positive"
              />
              <StatCard
                label="Total spending"
                value={formatCurrency(totals.spending)}
                sublabel="All categories"
                tone="warning"
              />
              <StatCard
                label="Current day type"
                value={lastDay?.day_type || "-"}
                sublabel={lastDay?.date || ""}
              />
            </div>
            <SafetyMeter daysSafe={state?.safety?.days_safe} />
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Earnings trend</h2>
              <span>Daily earnings</span>
            </div>
            <LineChart data={trendData} labels={summaryDays.map((d) => d.date)} />
            <div className="footer-note">Projected month earnings uses the last 7 days average.</div>
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Spending mix</h2>
              <span>Categories</span>
            </div>
            <BarChart data={spendData} />
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Notices</h2>
              <span>Actions to take</span>
            </div>
            <NoticeList items={notices} />
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Schemes and loans</h2>
              <span>Eligibility</span>
            </div>
            <div className="split">
              <SchemeList userId={userIdNumber} onRefresh={refreshAll} />
              <LoanList userId={userIdNumber} onRefresh={refreshAll} />
            </div>
          </section>
        </div>

        <div>
          <section className="section">
            <div className="section-title">
              <h2>Profile setup</h2>
              <span>Create a demo user</span>
            </div>
            <div className="form">
              <div className="form-row">
                <input
                  name="name"
                  value={profile.name}
                  onChange={handleProfileChange}
                  placeholder="Name"
                />
                <select name="language" value={profile.language} onChange={handleProfileChange}>
                  <option value="hindi">Hindi</option>
                  <option value="kannada">Kannada</option>
                </select>
              </div>
              <div className="form-row">
                <select name="platform" value={profile.platform} onChange={handleProfileChange}>
                  <option value="swiggy">Swiggy</option>
                  <option value="zomato">Zomato</option>
                </select>
                <input
                  name="mandatory_spend"
                  value={profile.mandatory_spend}
                  onChange={handleProfileChange}
                  placeholder="Mandatory weekly spend"
                />
              </div>
              <div className="form-row">
                <input
                  name="household_obligation"
                  value={profile.household_obligation}
                  onChange={handleProfileChange}
                  placeholder="Household obligation"
                />
                <input
                  name="current_savings"
                  value={profile.current_savings}
                  onChange={handleProfileChange}
                  placeholder="Current savings"
                />
              </div>
              <div className="form-row">
                <input
                  name="age"
                  value={profile.age}
                  onChange={handleProfileChange}
                  placeholder="Age"
                />
                <input
                  name="annual_income"
                  value={profile.annual_income}
                  onChange={handleProfileChange}
                  placeholder="Annual income"
                />
              </div>
              <button onClick={createUser}>Create user</button>
              <div className="footer-note">
                Creating a new user updates the user id in the toolbar.
              </div>
            </div>
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Manual inputs</h2>
              <span>Log earnings and spending</span>
            </div>
            <ManualEarningForm userId={userIdNumber} onSaved={refreshAll} />
            <ManualSpendingForm userId={userIdNumber} onSaved={refreshAll} />
            <SmsParseForm userId={userIdNumber} onSaved={refreshAll} />
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Event ingestion</h2>
              <span>Part B will hit this</span>
            </div>
            <EventIngestForm userId={userIdNumber} onSaved={refreshAll} />
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Purchase simulator</h2>
              <span>Impact check</span>
            </div>
            <PurchaseSimulator userId={userIdNumber} />
          </section>

          <section className="section">
            <div className="section-title">
              <h2>Chat assistant</h2>
              <span>Hindi or Kannada</span>
            </div>
            <ChatPanel userId={userIdNumber} />
          </section>
        </div>
      </div>
    </div>
  );
}
