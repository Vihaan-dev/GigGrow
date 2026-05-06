# GigShield

**A financial-resilience copilot for India's 153M gig workers.**

Daily-resolution earnings tracking, SMS-parsed spend analysis, day-of-week forecasting, government-scheme matching, and proactive AI nudges — in Hindi, Kannada, and English.

> Built for the **AIC × Anthropic Claude Hackathon** (Track 3 — Economic Empowerment & Education).

---

## TL;DR

| | |
|---|---|
| **The user** | Ramesh — Swiggy delivery partner in Whitefield, Bengaluru. ₹18–28k/month volatile income. ₹15k moneylender loan at 60% APY. Wants a second-hand bike. |
| **The gap** | Banking apps need a salary slip. Fintech apps assume credit history. Govt schemes exist but nobody tells gig workers they qualify. Financial literacy material is in English. |
| **What GigShield does** | Auto-tracks earnings, parses bank SMS in-memory, forecasts next 14–30 days, simulates big purchases, surfaces eligible schemes/loans, and nudges in the user's language. |
| **What it's not** | Not regulated financial advice. Not a chatbot wrapper. Not free of failure cases (and we're honest about which users we fit poorly). |

---

## How this maps to the rubric

The four evaluation criteria — Impact (25), Technical (30), Ethical (25), Presentation (20) — each have a dedicated section below. Judges should be able to score every criterion within 5 minutes of reading.

| Criterion | Where in this README |
|---|---|
| **Impact Potential** | [§ The problem](#the-problem) · [§ Personas](#personas-three-distinct-financial-lives) · [§ 90-day outcome](#quantified-outcome) |
| **Technical Execution** | [§ Architecture](#architecture) · [§ AI integration](#ai-integration--how-its-not-a-chatbot-wrapper) · [§ Forecast model & validation](#forecast-model--honest-validation) · [§ Test suite](#test-suite) |
| **Ethical Alignment** | [§ Ethical framework](#ethical-framework) · [§ What we never store](#what-we-never-store) · [§ Decision sovereignty](#decision-sovereignty) |
| **Presentation** | [§ Quick start](#quick-start) · [§ In-app product tour](#in-app-product-tour) |

---

## The problem

India has **153M gig workers** — delivery partners, auto drivers, freelancers — powering the new economy yet invisible to its financial infrastructure.

| Pain | Reality |
|---|---|
| **No income visibility** | Earns ₹400 one day, ₹1,800 the next. No way to plan. |
| **No safety buffer** | ~60% have less than ₹5,000 in savings. One bad week → debt spiral. |
| **Locked out of formal credit** | Banks need salary slips. NBFCs charge 36%+ APR with steep KYC. |
| **Govt schemes unused** | PM-KISAN (₹6,000/yr), PMSBY (₹2L cover for ₹20/yr) exist — but nobody tells gig workers they qualify. |
| **Predatory credit fills the gap** | Local moneylenders at 60% APY are the only available option. |
| **Financial advice is English, urban, salaried** | Completely irrelevant to Ramesh from Whitefield. |

GigShield is built specifically for this user. Not a generalised personal-finance app retro-fitted for low-income markets.

---

## Solution architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  React + Vite frontend  (Web Speech API for hi-IN/kn-IN/en-IN)  │
└─────────────────────────────────────────────────────────────────┘
                              │  REST + JSON
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flask backend  (≈ 30 endpoints, JSON-file storage)             │
├─────────────────────────────────────────────────────────────────┤
│  Intelligence layer:                                             │
│   • profile_insights.py   DOW pattern · CV · streaks · category │
│   • forecast.py           per-day prediction × 3 scenarios       │
│   • backtest.py           hold-out validation (MAE/R²/coverage)  │
│   • outcome.py            current-vs-GigShield 90d projection    │
│   • briefing.py           Gemini-narrated summary, validated     │
│   • nudges.py             rule-based triggers + LLM phrasing     │
│   • explain_day.py        click-day anomaly explanation          │
│   • chat_tools.py         2-pass tool-use chat                   │
│   • crisis.py             debt-spiral score + NGO helplines      │
│   • digest.py             weekly WhatsApp digest preview         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI layer:  Gemini (gemini-2.5-flash via google-generativeai)    │
│  Used for:                                                       │
│   • Briefing composition (validated, no hallucinated numbers)    │
│   • Day-click anomaly explanation                                │
│   • Tool-use chat: tool selection + answer composition           │
│   • SMS disambiguation (only when regex confidence < 80)         │
│  Every call has a deterministic fallback.                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Simulation layer  (replay of 30-day events for the demo)        │
│   simulation/seed_personas.py · simulation/run_sim.py            │
└─────────────────────────────────────────────────────────────────┘
```

**Why JSON-file storage:** The hackathon scope is one machine, three demo personas, no concurrency. SQLite was the alternative; JSON is faster to seed and inspect. Production migration path is documented in [§ Roadmap](#roadmap).

---

## AI integration — how it's not a chatbot wrapper

Five distinct uses of the LLM, each doing real work that wouldn't fit a regex.

### 1. Auto-narrated dashboard briefing
Gemini reads a structured snapshot of the user's last 30 days plus their forecast and 90-day outcome, and writes a 4-sentence briefing in the user's language.

**Hallucination guard:** Every rupee value Gemini mentions is checked against the snapshot's allowed-numbers set. If the response cites any unallowed number, the briefing is **rejected** and we fall back to deterministic copy. This is enforced in `_validate_briefing()` in [`backend/services/briefing.py`](backend/services/briefing.py).

### 2. Tool-use chat (2-pass loop)
The chat endpoint is **not** "shove user message + context into LLM and pray." It runs two passes:

```
Pass 1 — Tool selection
  user message + tool catalog → Gemini → JSON: { tool_calls: [...] }

Pass 2 — Answer composition
  for each tool: backend.execute(name, args) on real data
  results + user message → Gemini → final answer in user's language
```

Tool catalog (8 tools, in [`backend/services/chat_tools.py`](backend/services/chat_tools.py)):
- `get_earnings_for_period(period)` · `get_spending_by_category(period)` · `get_dow_pattern()`
- `get_safety_status()` · `get_forecast(days, scenario)` · `simulate_purchase(amount)`
- `match_schemes()` · `top_overspend()`

The tool selections are **shown in the chat UI** above each answer — judges see exactly which data the model retrieved before responding.

### 3. Click-day anomaly explanation
Click any day on the timeline → backend computes the day's z-score against its day-of-week mean, fetches event multipliers (rain/holiday/surge), and asks Gemini to explain in 2-3 sentences. Same hallucination guard as the briefing.

Sample output (deterministic fallback when no LLM key):
> *"2026-05-02 (Sat): earned Rs 1,050, spent Rs 223. That is below the Sat average of Rs 1,724 (z = -1.5σ). Events recorded: weather_rain."*

### 4. Proactive nudges
Rule-based triggers detect five conditions: overspend, earnings dip, low safety, scheme opportunity, best-day uplift. Gemini phrases each trigger as a short message in the user's language. Each nudge has a **"Why am I seeing this?"** toggle that exposes the trigger formula, the data the rule used, and the source endpoint.

### 5. SMS disambiguation
Regex parser tags merchants/categories deterministically. When confidence falls below 80 *and* category is "other" *and* amount > ₹50, Gemini is asked to classify between {fuel, food, rent, transfer, utilities, income, other}. Cached per-SMS so the demo doesn't burn API quota.

---

## Forecast model & honest validation

The forecast is intentionally simple and inspectable:

```
predicted_earnings[d] = day_of_week_mean(d.dow) × Π event_multiplier(events_on(d))

  where  event_multiplier:
    weather_rain:  ×0.65
    holiday:       ×0.55
    low_demand:    ×0.75
    surge_bonus:   ×1.40

  scenarios:
    optimistic   = base + 1·σ
    baseline     = base
    pessimistic  = base - 1·σ
```

Spending forecast = per-category daily baseline + scheduled monthly hits (rent, transfer detected by day-of-month).

### Backtest (hold-out validation)
We trained the DOW model on the first 23 days, predicted the last 7, and reported errors. Numbers across the three demo personas:

| Persona | MAE | MAE % of mean | R² | 1σ coverage | Verdict |
|---|---|---|---|---|---|
| **Ramesh** (Swiggy delivery) | ₹149 | **12.6 %** | 0.57 | 71.4 % | Strong fit — DOW pattern works |
| **Lakshmi** (Pune auto driver) | ₹300 | 28.1 % | -1.15 | 57.1 % | Fair — surge-on-rain breaks DOW assumption |
| **Vikram** (freelance writer) | ₹4,523 | **129.4 %** | -1.16 | 28.6 % | Poor fit — invoice-driven income needs a different model class |

We surface this honestly in the UI via a `ConfidenceCaveat` chip on every forecast and outcome. Vikram's outcome is labelled *"Forecast: low confidence — rough estimate."* This is intellectual honesty, not a flaw — knowing where your model fails is the first step to deploying it safely.

---

## Quantified outcome

For each user, GigShield computes a 90-day projection comparing **current trajectory** vs **GigShield plan**. The plan applies four transparent levers:

1. **Cap the worst overspend category** — bring last-7-day daily average back to the 30-day baseline (50% capture)
2. **Lean into the best day-of-week** — capture 25% of the weekly best-day uplift
3. **Refinance high-APY debt** — if a matched loan beats the moneylender APY
4. **Enrol in cheap schemes** — PMSBY (₹20/yr) + PMJJBY (₹436/yr) for ₹4L of cover

### Ramesh's 90-day outcome (live numbers from `GET /api/outcome/1`)

|  | Current path | GigShield plan | Delta |
|---|---|---|---|
| **Ending savings** | ₹71,598 | ₹75,842 | **+₹4,244** |
| **Days safe (end)** | 41.8 | 44.2 | +2.5 |
| **Interest paid (90d)** | ₹2,250 | ₹450 | **₹1,800 avoided** |
| **Insurance cover added** | — | ₹4,00,000 | — |

Concrete actions in Ramesh's plan:
1. *Cap food spend back to baseline — saves ~₹12/day = ₹1,080 over 90 days.*
2. *Lean into Saturday surge zones — capture 25% of weekly uplift = ₹1,476.*
3. *Refinance moneylender to KGFS — drops APY 60% → 12%. Saves ₹1,800 interest.*
4. *Enrol in PMSBY + PMJJBY — costs ₹112 for 90 days, covers ₹4,00,000 downside.*

This is the impact number a judge can quote: **GigShield's plan moves Ramesh from a 60% APY moneylender debt spiral to a financially literate trajectory, in 90 days, with deterministic math the user can audit.**

---

## Personas — three distinct financial lives

Demo data (deterministic, seeded by [`simulation/seed_personas.py`](simulation/seed_personas.py)) covers three structurally different earning patterns:

| | **Ramesh** | **Lakshmi** | **Vikram** |
|---|---|---|---|
| Job | Swiggy delivery | Rapido auto driver | Freelance writer |
| City | Whitefield, BLR | Hinjewadi, Pune | HSR Layout, BLR |
| Language | Hindi | Hindi | English |
| Avg daily earning | ₹1,231 | ₹911 | ₹2,638 |
| Volatility (CV) | 0.35 | 0.34 | **1.50** |
| Pattern | Weekend uplift | Surge on rain | Lumpy invoice days |
| Mandatory monthly | ₹12,000 | ₹8,000 | ₹15,000 |
| Current savings | ₹13,700 | ₹6,500 | ₹22,000 |
| Moneylender debt | ₹15,000 @ 60% | ₹8,000 @ 48% | none |
| Goal | Bike ₹22,000 | School fees ₹35,000 | 6-month buffer |
| GigShield 90-day delta | +₹4,244 | +₹992 | +₹5,384 |

A persona switcher in the header lets judges flip between them — the dashboard reshapes itself: Ramesh's bar chart shifts, Lakshmi's surge-on-rain icons appear, Vikram's lumpy zero-then-spike pattern becomes obvious. **One system, three lives.**

---

## Ethical framework

The proposal makes claims about ethics. The code makes those claims falsifiable.

### What we store
| Kind | Persisted fields |
|---|---|
| **Account** | name, language, occupation, city, monthly mandatory spend, current savings, age, annual income |
| **Earnings** | date, amount, deliveries count, platform |
| **Spending** | date, amount, category, source (sms/manual), parsed merchant if extracted |
| **Events** | type, date, redacted summary (≤80 chars), parsed merchant/confidence |

### What we never store
- **Raw SMS message text** — parsed in memory by [`backend/services/sms_parser.py`](backend/services/sms_parser.py), then discarded
- **Phone numbers, account digits, OTPs** — redacted to `###` before storage by `_redact()` in [`backend/services/events.py`](backend/services/events.py)
- **Location data, device identifiers, contact list** — never collected
- **Loan referral commissions or platform partnership flags** — not in the schema

These are tested, not just claimed. See [`backend/tests/test_privacy.py`](backend/tests/test_privacy.py):
- `test_sms_event_does_not_persist_raw_text` — searches the entire post-ingest store for SMS framing markers
- `test_non_sms_summary_is_redacted` — asserts phone numbers and account digits become `###`
- `test_sms_event_has_no_summary_field_filled` — SMS events get **only** structured fields

### Decision sovereignty
Every recommendation is followed by *"GigShield's suggestion. The decision is yours."* The system never auto-applies for a loan, never auto-enrols in a scheme, never sends SMS or makes calls.

### Provenance on every AI output
- **Briefing** has a *"Show source data the model saw"* toggle exposing the full snapshot
- **Nudges** have a *"Why am I seeing this?"* toggle exposing the trigger formula and source endpoint
- **Day explanation** drawer exposes the z-score, day-of-week expectation, and listed events
- **Chat answers** show every tool call and its arguments before the response

### Crisis escalation
When debt-spiral score ≥ 2 (4 signals: low days_safe, spend > earn, ≥4-day low streak, savings < ¼ month), the dashboard shows a red banner with **independent NGO helplines**:

| Org | Type | Phone | Languages |
|---|---|---|---|
| iCall (TISS) | Psychosocial counselling | +91 9152987821 | English, Hindi, Marathi, Kannada |
| Snehi | Emotional support | +91 9582208181 | English, Hindi |
| RBI CMS | Predatory lending grievance | 14448 | English, Hindi |
| MoneyLife Foundation | Financial counselling | +91 9869913444 | English, Hindi |

The footer also surfaces these on *every* page (not just crisis-triggered) under *"Need to talk to someone?"*

### Right of access, right to be forgotten
Every user can:
- `GET /api/export/<uid>` — download their full data as JSON, including a `data_minimalism_note`
- `POST /api/forget/<uid>` — wipe all data with a typed *"I confirm"* phrase, optional `hard:true` to remove the account too

UI lives at the **Privacy** section of the dashboard.

---

## API surface

30 endpoints. Listed by domain:

### User & account
- `POST /api/users` · `GET /api/users` · `GET /api/users/<uid>`
- `GET /api/export/<uid>` — full data dump (right of access)
- `POST /api/forget/<uid>` — wipe data, optionally remove account
- `POST /api/reset` — wipe entire store (demo only)

### Earnings, spending, events
- `POST /api/earnings/log` · `GET /api/earnings/<uid>?days=N`
- `POST /api/spending/log` · `POST /api/spending/parse-sms` · `GET /api/spending/<uid>?days=N`
- `POST /api/events/ingest` · `GET /api/events/<uid>?days=N`

### Intelligence layer
- `GET /api/insights/<uid>?days=30` — DOW pattern, category mix, volatility, streaks
- `GET /api/timeline/<uid>?days=30&forecast=14` — combined per-day chart data
- `GET /api/forecast/<uid>?days=30&scenario=baseline|optimistic|pessimistic`
- `GET /api/backtest/<uid>?holdout=7` — hold-out validation with MAE/R²/coverage
- `GET /api/outcome/<uid>?days=90` — current path vs GigShield plan
- `GET /api/safety/<uid>` — days-safe + status
- `GET /api/state/<uid>` — combined snapshot
- `GET /api/summary/<uid>?days=N`

### AI-powered features
- `GET /api/briefing/<uid>?language=en|hi|kn` — Gemini-narrated, validated
- `GET /api/explain-day/<uid>?date=YYYY-MM-DD&language=…` — click-day explanation
- `GET /api/nudges/<uid>?language=…` — proactive nudges in user language
- `POST /api/chat` — 2-pass tool-use chat
- `POST /api/purchase/simulate` — 3-option output + 30d cash-runway

### Schemes, loans, distribution
- `POST /api/schemes/match` · `GET /api/schemes/all`
- `POST /api/loans/match` · `GET /api/loans/all`
- `GET /api/digest/<uid>` — weekly WhatsApp digest preview
- `POST /api/digest/subscribe`
- `GET /api/crisis/<uid>` — debt-spiral score + NGO helplines

---

## Quick start

### Prerequisites
- Python 3.10+ · Node.js 18+ · npm

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Optional: enable Gemini-powered briefing/chat/explanations
echo "GEMINI_API_KEY=your_key_here" > .env

# Port 8000 is the default; pick another if it's taken on your box
PORT=8088 python3 app.py
```

The backend boots with deterministic fallbacks — every Gemini-powered feature falls back to a sensible deterministic output when no API key is set, so the demo works **without a key**.

### Frontend
```bash
cd frontend
npm install

# Point to your backend port
echo "VITE_API_BASE=http://127.0.0.1:8088" > .env.local

npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`).

### Demo data
The store is pre-seeded with three personas. To re-seed:

```bash
cd simulation

# Direct (writes store.json — no server needed)
python3 seed_personas.py

# OR via the live API
python3 seed_personas.py --base-url http://127.0.0.1:8088
```

---

## In-app product tour

First-time visitors get a 10-step guided overlay that spotlights each section:

1. Welcome
2. AI briefing
3. Snapshot KPIs
4. Smart nudges
5. 90-day outcome
6. Daily timeline
7. Forecast + backtest
8. Schemes & loans
9. Privacy controls
10. Tool-use chat (top nav)

Built in [`frontend/src/components/Tour.jsx`](frontend/src/components/Tour.jsx). Replayable any time from the **✨ Tour** button in the header. Auto-show is gated by `localStorage.gigshield_tour_seen`.

---



## Test suite

```bash
cd backend
python3 -m pytest
```

**45 tests, ~0.9 seconds.** Coverage:

| File | Tests | Asserts |
|---|---|---|
| `test_profile_insights.py` | 5 | DOW computation, weekend uplift, best/worst symmetry |
| `test_forecast.py` | 5 | Horizon respect, scenario ordering, purchase delta = amount, planned-event multiplier |
| `test_outcome.py` | 4 | Savings delta non-negative, refinance reduces interest, days_safe scale sanity |
| `test_sms_parser.py` | 6 | Per-category extraction, income vs expense, low-confidence flag, error cases |
| `test_crisis.py` | 3 | Trigger threshold, helpline gating |
| `test_backtest.py` | 4 | Train/test split, per-day rows, short-history error |
| `test_privacy.py` | 4 | **Raw SMS never persists**, summary redaction, summary truncation |
| `test_endpoints_privacy.py` | 5 | Export shape, forget confirmation, soft vs hard delete |

The privacy tests are the most important ones in the suite. If they break silently, our public claim ("no raw SMS stored") becomes false. They guard a contract, not just a function.

---

## What's intentionally out of scope

These were scoped down deliberately to fit the hackathon timeline:

- **Real Swiggy/Zomato/Rapido API integration** — mocked. Production hook points are documented in [`backend/services/events.py`](backend/services/events.py).
- **SMS read permission on Android** — not in scope for a web app. Manual SMS paste form is provided.
- **One-tap loan/scheme application** — every CTA links to the official application URL. We do **not** auto-fill or earn referral commissions.
- **Multi-tenant production deployment** — JSON file storage, single-machine.
- **Encryption at rest** — claimed in proposal, deferred (sqlcipher migration in roadmap).
- **WhatsApp Business API** — digest endpoint generates a preview; sending is mocked.

---

## Roadmap

| Quarter | Item |
|---|---|
| Now → +1 mo | Real Swiggy/Zomato API connectors. Migration to PostgreSQL with row-level encryption. |
| +1 → +3 mo | Twilio-backed weekly WhatsApp digest delivery. Native Android app with SMS read. |
| +3 → +6 mo | Tier-2/3 city expansion. 8-language support. Auto-fill scheme applications via partnerships. |
| +6 → +12 mo | A second-tier forecaster for lumpy-income freelancers (invoice-driven). Bias audit across gender / city-tier / platform. |

---

## Tech stack

| Layer | Tech | Cost |
|---|---|---|
| LLM | Gemini 2.5 Flash (`google-generativeai`) | Free tier sufficient for demo |
| Backend | Flask 3 + flask-cors + python-dotenv | Free |
| Frontend | React 18 + Vite 5 (no UI library — handcrafted SVG charts) | Free |
| Voice I/O | Web Speech API (browser-native, hi-IN / kn-IN / en-IN) | Free |
| Storage | JSON file with atomic writes | Free |
| Tests | pytest 9 | Free |
| Hosting (post-hackathon) | Vercel (frontend) + Render (backend) | Free tiers sufficient |

---

## Repository layout

```
GigGrow-main/
├── README.md                          # this file
├── MVP.md                             # one-day MVP scope (historical)
├── README_PRODUCT.md                  # product spec (long-form)
├── README_BUILD.md                    # build guide (long-form)
├── AIC × Anthropic Claude Hackathon.pdf
├── GigShield_Proposal.pdf
├── backend/
│   ├── app.py                         # Flask app, ~30 endpoints
│   ├── storage.py                     # JSON-file store with atomic writes
│   ├── requirements.txt
│   ├── services/                      # the intelligence layer
│   │   ├── profile_insights.py
│   │   ├── forecast.py
│   │   ├── backtest.py
│   │   ├── outcome.py
│   │   ├── briefing.py
│   │   ├── nudges.py
│   │   ├── explain_day.py
│   │   ├── chat_tools.py
│   │   ├── crisis.py
│   │   ├── digest.py
│   │   ├── sms_parser.py
│   │   ├── events.py
│   │   ├── safety.py
│   │   ├── analytics.py
│   │   ├── schemes.py
│   │   ├── loans.py
│   │   └── gemini_client.py
│   ├── tests/                         # 45 passing tests
│   │   ├── test_profile_insights.py
│   │   ├── test_forecast.py
│   │   ├── test_outcome.py
│   │   ├── test_sms_parser.py
│   │   ├── test_crisis.py
│   │   ├── test_backtest.py
│   │   ├── test_privacy.py
│   │   └── test_endpoints_privacy.py
│   ├── data/store.json                # JSON-file persistence
│   └── pytest.ini
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                    # router + dashboard composition
│       ├── api.js                     # frontend API client
│       ├── styles.css                 # design system
│       └── components/
│           ├── Briefing.jsx           ConfidenceCaveat.jsx
│           ├── DailyTimeline.jsx      DowChart.jsx
│           ├── CategoryDonut.jsx      VolatilityChip.jsx
│           ├── OutcomeCard.jsx        ForecastPanel.jsx
│           ├── BacktestStat.jsx       NudgeCards.jsx
│           ├── ChatPanel.jsx          PurchaseSimulator.jsx
│           ├── SchemeList.jsx         LoanList.jsx
│           ├── PersonaSwitcher.jsx    DigestSubscribe.jsx
│           ├── PrivacyPanel.jsx       HelplineFooter.jsx
│           ├── CrisisBanner.jsx       Tour.jsx
│           ├── LlmStatusBadge.jsx     ProfileSettings.jsx
│           └── …
└── simulation/
    ├── seed_personas.py               # 3-persona deterministic seeder
    ├── run_sim.py                     # day/week/month event replay
    └── data/events.json
```

---

## Acknowledgements

- **The 153 million gig workers** whose financial reality drove every design decision.
- **Independent NGOs** (iCall, Snehi, RBI CMS, MoneyLife Foundation) whose helplines we surface — without commissions and without permission, because the public phone numbers exist for exactly this reason.
- **Anthropic + AIC** for the prompt that shipped a project that *should* exist.

---

## Critical questions, answered

> **Who are you building this for and why do they need it?**
> 153 million Indian gig workers, embodied by Ramesh. They power the new economy and remain invisible to its financial infrastructure. Existing tools assume salary slips and credit history; Ramesh has neither. He has SMS-based bank alerts and an unstable income.

> **What could go wrong and what would you do about it?**
> *Bad financial advice.* — Every recommendation is labelled informational. Math is deterministic and the user can audit it. Crisis states surface NGO helplines. We do not auto-apply for loans.
> *Predatory referral economy.* — Schemes/loans link to official URLs only. No commissions, no platform partnerships. Stated in the UI, twice.
> *Hallucinated numbers.* — Briefing and explain-day responses are post-validated against an allowed-numbers set. Out-of-bounds numbers trigger the deterministic fallback.
> *Bias.* — Backtest stats are surfaced honestly per user. Lakshmi's MAE is reported as 28% with a "fair fit" chip. Vikram's is reported as 129% with a "poor fit — rough estimate" chip. We don't paper over failure modes.

> **How does this help people rather than make decisions for them?**
> Every recommendation ends with *"GigShield's suggestion. The decision is yours."* The system never sends SMS, never makes calls, never auto-applies. It surfaces options, shows the math, and gets out of the way.

---

*Built for AIC × Anthropic Claude Hackathon, 2026. Track 3 — Economic Empowerment & Education.*
