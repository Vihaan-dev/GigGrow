# GigShield: Product Specification

**AIC x Anthropic Claude Hackathon 2025 | Track 3: Economic Empowerment & Education**

---

## 1. Product Overview

**GigShield** is a financial resilience co-pilot for India's 153M gig workers. It automatically tracks earnings, parses spending via SMS, calculates personalized safety buffers, sends intelligent nudges, and connects users to government schemes and microloans — all in Hindi/Kannada.

**Core Insight:** Financial tools exist for salaried professionals. Nothing exists for someone like Ramesh, a Swiggy delivery partner earning ₹400 one day, ₹1,800 the next, with zero safety buffer. GigShield changes that.

---

## 2. The User: Ramesh

- **Age:** 29 | **City:** Whitefield, Bengaluru | **Job:** Swiggy delivery partner
- **Income:** ₹18,000–₹28,000/month (highly volatile)
- **Expenses:** ₹7,000 rent + ₹4,000 fuel + ₹5,000 home transfer = ₹16,000 mandatory
- **Current state:** No bank savings, took a ₹15,000 moneylender loan at 5%/month
- **Pain point:** Wants to buy a second-hand bike (₹22,000) but doesn't know if he can afford it
- **Language:** Primarily Hindi/Kannada

**Why Ramesh matters:** He's 1 of 153M. Traditional finance completely ignores him.

---

## 3. Problem Statement

### The Gap

| What Exists | Who It's For | Why Ramesh Can't Use It |
|---|---|---|
| Banking apps | Salaried professionals | Needs salary slip to open account; transaction history useless (all cash) |
| Fintech loans (Cred, BNPL) | Credit card holders | Ramesh has no credit card, no salary |
| Personal finance apps (Mint, Monzo) | English speakers, stable income | Assumes income is predictable; no SMS parsing for cash-heavy ecosystem |
| Govt schemes (PM-KISAN, PMSBY) | Everyone (theoretically) | Nobody tells gig workers they exist; eligibility confusing |

### The Hard Truths

1. **Income volatility:** Ramesh earns differently every day. Traditional "emergency fund = 6 months salary" is meaningless.
2. **Invisible spending:** ~60% of gig worker spending is cash. Banks see nothing. Ramesh doesn't remember where ₹3,000 went.
3. **No financial identity:** No salary slip, no credit history, no path to formal loans.
4. **Predatory credit:** Moneylenders at 60% APY are the only option. Microfinance exists (18–24% APY) but requires information Ramesh doesn't have.
5. **Language barrier:** Financial advice in English is useless. Even if Ramesh reads English, the jargon ("liquidity ratio," "MER") is alien.

---

## 4. Solution Architecture

### What GigShield Does (Not a Chatbot Wrapper)

GigShield combines **three intelligent systems:**

#### A. **Earnings Tracker**
- Auto-syncs earnings from Swiggy/Zomato API (mock for demo; production-ready hooks)
- Fallback: Screenshot paste or simple text log ("Earned 1200 today")
- Stores daily earnings with timestamp
- Calculates: Daily average, weekly trend, volatility (standard deviation)

#### B. **Smart Spend Analyzer**
- **SMS Parser:** Reads bank transaction alerts (HDFC, Axis, SBI, ICICI formats)
- **Claude-powered:** Disambiguates ambiguous txns ("Swiggy Technologies Ltd" → income, not expense)
- **Auto-categories:** Fuel, Food, Rent, Transfer, Entertainment, Other
- **Handles cash gaps:** User can log cash spending (fuel from local pump, food from restaurant)
- **Calculates:** Weekly spend cap, alerts on overspend

#### C. **Safety Buffer Calculator**
- Analyzes 30/60-day earnings + spending patterns
- Computes: Income variance (std dev), average deficit weeks
- **Outputs personalized safety target:**
  - "Your income varies ±₹250/day. To survive a 10-day dry spell, you need ₹5,000. You have ₹3,200 → 6 days safe."
- **Gamified tracking:** Resilience score (0–100%), progress bar

#### D. **Proactive Alert Engine**
- Detects anomalies: "Fuel spend is 35% above weekly average"
- Nudges: "Skip 2 deliveries today or refuel at cheaper pump"
- **Big purchase simulator:** User says "I want to buy a phone for ₹2,000" → System shows impact on safety
- **Weekly digests:** Wins, warnings, progress

#### E. **Government Scheme Matcher**
- Cross-checks Ramesh's profile against:
  - **PM-KISAN:** ₹6,000/year, eligibility based on income
  - **PMSBY (Pradhan Mantri Suraksha Bima Yojana):** ₹2L accident insurance, ₹20/year
  - **PMJJBY:** ₹2L life insurance, ₹436/year
  - **Ujjivan microloans:** ₹5K–₹50K at 18–22% APY
- Shows: "You qualify for X. Here's what you need to apply."

#### F. **Loan Eligibility Display**
- Scrapes/displays 3–4 microfinance options (Ujjivan, KGFS, local NBFCs)
- Shows: APY, tenure, amount eligible for
- **No auto-fill for hackathon scope** (future: one-tap application)
- Goal: Ramesh walks into a bank informed, not confused

#### G. **Conversational Interface (Claude)**
- User speaks/types in Hindi or Kannada: "Kal kitna kamaya?" (How much did I earn yesterday?)
- Claude parses intent, calls backend logic, responds in same language
- Examples:
  - "Can I afford the bike?" → Claude explains financial impact in human terms
  - "What's PM-KISAN?" → Claude explains eligibility + application steps
  - "Why is my fuel spend so high?" → Claude analyzes patterns, suggests solutions

---

## 5. User Flow

### Happy Path: Day 1–7

**Day 1: Onboarding**
1. Ramesh opens PWA (Progressive Web App)
2. Chooses language: Hindi / Kannada
3. Connects Swiggy account OR grants SMS read permission
4. Sets mandatory expenses: Rent ₹7,000 | Home transfer ₹5,000
5. System says: "Got it. Your must-have is ₹12,000. Target earnings: ₹15,000/week."

**Day 2–5: Auto-Sync**
- Every evening, Swiggy earnings auto-pull
- Bank SMS parsed in background
- Ramesh sees: "Earned ₹1,240 today | Balance: ₹4,300 | Fuel spend: 80% of cap"

**Day 6: Alert Fires**
- Fuel spend goes ₹650 (over ₹600 weekly cap by ₹50)
- Notification (in Hindi): "Fuel ₹650 this week. Target ₹600. Tomorrow, use the surge-hour areas near Koramangala to make extra ₹800 and offset."

**Day 7: Big Decision**
- Ramesh wants to buy a used bike for ₹22,000
- He taps "Plan a purchase"
- Types (voice): "Used bike 22000"
- **GigShield response:**
  - "Your current safety: 8 days"
  - "After bike: 3 days (⚠️ risky)"
  - "Plan A: Work 18 extra days. Earn ₹1,500/day → ₹27K → use ₹22K → safety stays at 8 days"
  - "Plan B: Apply for Ujjivan bike loan. ₹22K at 18% → ₹180/month. Your cash-flow allows ₹250/month buffer."
  - **Button:** "Show me how to apply for Ujjivan"

---

## 6. Core Features Breakdown

### Feature 1: Auto Earnings Sync
**Purpose:** Eliminate manual data entry  
**Input:** Swiggy API (mocked for demo) or manual screenshot/text  
**Output:** Daily earnings record with timestamp  
**Claude Role:** None (pure backend)

**Example:**
```
Input: Swiggy API returns { date: "2025-05-05", amount: 1240, deliveries: 8 }
Output: Dashboard shows "₹1,240 | 8 deliveries | Avg: ₹155/delivery"
```

---

### Feature 2: SMS-Based Spend Tracking
**Purpose:** Capture bank spending (the visible 40% of gig worker cash flow)  
**Input:** Raw SMS text from banks (or screenshot of SMS)  
**Output:** Auto-categorized transaction with confidence score  
**Claude Role:** Disambiguate ambiguous entries

**Example:**
```
Input SMS: "HDFC: Debit ₹600 at Sunbeam Petrol Pump, Whitefield. Bal ₹4,200"
Output: Category=Fuel | Amount=600 | Confidence=99% | Verified=true

Input SMS: "HDFC: Debit ₹500 at Swiggy Supermarket, Bengaluru. Bal ₹3,700"
Claude Query: "Is this food (personal expense) or supplies for selling?"
Claude Response: "Based on 'Supermarket' and user's delivery job, likely personal food. Category: Food"
Output: Category=Food | Amount=500 | Confidence=85% | ManualVerifyFlag=true (user confirms)
```

---

### Feature 3: Safety Buffer Calculator
**Purpose:** Tell Ramesh "how many days can you survive with zero income"  
**Input:** 30/60-day earnings + spending history  
**Output:** Personalized safety target + current status + progress path

**Algorithm:**
```
1. Calculate daily earnings average (last 30 days)
2. Calculate daily earnings std dev (volatility)
3. Define "worst week" = average - (2 × std_dev)
4. Calculate weekly deficit days = max(0, (mandatory_spend - worst_week) / daily_avg)
5. Recommend safety fund = (deficit_days + buffer_days) × daily_avg
6. Current status = savings_balance / recommended_safety
7. Days_safe = savings_balance / daily_mandatory_spend

Example (Ramesh):
- Avg earnings: ₹2,500/day
- Std dev: ₹250
- Worst week avg: ₹1,750/day
- Mandatory spend: ₹1,714/day (₹12,000/7)
- Worst week deficit: (1714 - 1750) = -₹36/day (actually surplus, but volatile)
- Safety target: 30 days × 1714 = ₹51,420 (conservative, accounts for volatility)
- Current savings: ₹3,200
- Days safe: 3200 / 1714 ≈ 1.8 days (⚠️ at risk)
```

---

### Feature 4: Proactive Alerts & Nudges
**Purpose:** Intervene before financial crisis  
**Input:** Daily earnings + spend + historical patterns  
**Output:** Contextual alerts in Hindi/Kannada  
**Claude Role:** Write nudges in empathetic, actionable language

**Alert Types:**

| Alert Type | Trigger | Nudge (Claude-generated) |
|---|---|---|
| Low Earnings | This week ₹2,000 below avg | "This week is 20% below normal. Peak hours are 11AM–2PM and 7PM–10PM. Try those zones Friday–Sunday." |
| Overspend | Fuel >110% of weekly cap | "Fuel spend ₹680 (cap ₹600). Tomorrow, plan routes more efficiently or refuel at cheaper pump in JP Nagar." |
| Safety Dropping | Buffer <3 days | "⚠️ You have 2 days of safety left. Work 5 extra shifts this week to rebuild buffer to 7 days." |
| Big Purchase | User logs purchase intent | [See Feature 4b below] |
| Scheme Eligible | User's profile matches govt scheme | "You qualify for PM-KISAN (₹6,000/year). Apply here [link]. Docs needed: Aadhar, bank statement." |

---

### Feature 4b: Big Purchase Simulator
**Purpose:** Help Ramesh make informed decisions on major expenses  
**Input:** Purchase amount + current safety buffer  
**Output:** Impact analysis + alternatives

**Flow:**
```
User: "I want to buy a bike for ₹22,000"
System: 
  1. Current safety: 8 days (₹13,700)
  2. After purchase: 3 days (₹5,140) ← RISKY
  3. Impact: Safety drops by 5 days
  
  Options:
  A) Work 15 extra days @ ₹1,500/day = ₹22,500 → Buy bike → Safety stays 8 days
  B) Get Ujjivan loan ₹22K @ 18% APY → ₹180/month EMI → You can afford it
  C) Delay 3 months, save ₹700/month → Buy bike → Safety stays 8 days
  
Recommendation: Option B is fastest. Want to apply?
```

---

### Feature 5: Government Scheme Eligibility
**Purpose:** Connect Ramesh to ₹6,000–₹2,00,000 safety nets he doesn't know about  
**Input:** Ramesh's income profile  
**Output:** Matched schemes + eligibility status + application link

**Schemes (for India):**

| Scheme | Coverage | Annual Cost | Eligibility | GigShield Check |
|---|---|---|---|---|
| PM-KISAN | ₹6,000/year direct cash | Free | Farmers + some self-employed | Income <₹2L/year? Likely yes |
| PMSBY | ₹2L accident insurance | ₹20/year | All Indians | Age 18–70? Auto-eligible |
| PMJJBY | ₹2L life insurance | ₹436/year | All Indians | Age 18–55? Auto-eligible |
| Ujjivan | ₹5K–₹50K microloans | 18–22% APY | Self-employed, gig workers | Income-based eligibility |

**Example Output:**
```
Ramesh's Profile:
- Self-employed (delivery partner)
- Annual income ₹30,000
- Age 29

Matched Schemes:
1. ✅ PM-KISAN: ELIGIBLE
   - ₹6,000/year (₹500/month)
   - Docs: Aadhar, bank account
   - Apply here [link to sbi.gov.in]

2. ✅ PMSBY: ELIGIBLE
   - ₹2L accident insurance
   - ₹20/year
   - Auto-enrolled if you apply via SBI

3. ✅ PMJJBY: ELIGIBLE
   - ₹2L life insurance
   - ₹436/year
   - Apply here [link]

4. ⚠️ Ujjivan Microloans: LIKELY ELIGIBLE
   - ₹22,000 loan at 18% APY available
   - Need: Aadhar, bank statement (3 months), proof of income
   - Apply here [link to Ujjivan website]
```

---

### Feature 6: Loan Eligibility Display
**Purpose:** Show Ramesh realistic lending options (not just moneylenders at 60% APY)  
**Input:** Ramesh's income + credit profile (mocked for demo)  
**Output:** Side-by-side loan comparison

**Example:**
```
Loan Options for ₹22,000 (Bike):

| Lender | APY | Tenure | Monthly EMI | Total Cost | Eligibility |
|---|---|---|---|---|---|
| Local Moneylender | 60% | 12 mo | ₹2,000/mo | ₹26,000 | ✅ Approved |
| Ujjivan Microfinance | 18% | 24 mo | ₹870/mo | ₹20,880 | ✅ Approved |
| KGFS (Govt) | 12% | 36 mo | ₹631/mo | ₹22,716 | ⚠️ Pending docs |

GigShield Recommendation:
"Ujjivan saves you ₹5,120 vs moneylender. KGFS is cheapest but slower. 
Your cash-flow can handle ₹870/month. Apply for Ujjivan?"
```

---

### Feature 7: Conversational Interface
**Purpose:** Make financial data human-readable and actionable in Ramesh's language  
**Input:** User speech/text in Hindi or Kannada  
**Output:** Contextual response in same language

**Claude's Roles:**
1. **Intent parsing:** "Kal kitna kamaya?" → extract { intent: "earnings", timeframe: "yesterday" }
2. **Data retrieval:** Fetch yesterday's earnings from DB
3. **Natural response:** "Kal aapne ₹1,240 kamaye, 8 deliveries se. Ye aapke average se 15% zyada hai. Acha din tha!" (Yesterday you earned ₹1,240 from 8 deliveries. That's 15% above your average. Good day!)

**Example Conversations:**

```
User (Hindi): "Mujhe bike khareedni hai, ₹22,000 mein. Kar sakte ho kya?"
Claude Output: "Aapka current safety buffer 8 din ka hai. Agar aap bike ab buy karoge, 
ye 3 din reh jayega — bohot risk hai. 
Lekin agar Ujjivan se ₹22,000 ka loan lo @ 18% APY, to ₹870/month EMI aapke liye handle-able hai. 
Kya tum Ujjivan ke liye apply karna chahte ho?" 

Translation: "Your current safety is 8 days. If you buy the bike now, it'll drop to 3 days—too risky. 
But if you take a ₹22,000 Ujjivan loan at 18% APY, the ₹870/month EMI is manageable for you. 
Do you want to apply for Ujjivan?"
```

---

## 7. Why This is NOT Just a Chatbot Wrapper

| Aspect | "Just a Chatbot" | GigShield |
|---|---|---|
| Data | Retrieves static info | Auto-syncs live earnings, parses SMS, calculates financial metrics |
| Intelligence | Answers general questions | Personalizes recommendations based on Ramesh's unique income variance |
| Proactivity | Waits for user query | Sends alerts before crisis (fuel overspend, safety dropping) |
| Decisions | Explains options | Simulates outcomes (bike purchase impact) with numbers |
| Language | Translates to Hindi | Generates contextual nudges in Hindi that understand gig worker life |
| Integration | Talks about APIs | Actually integrates Swiggy, bank SMS, govt databases |

**Claude's real job:** Not to replace a financial advisor (impossible—Ramesh can't afford one). But to make financial data *understandable* in Ramesh's language and context.

---

## 8. Tech Stack (Free Tier)

| Layer | Technology | Why | Cost |
|---|---|---|---|
| **LLM** | Claude Sonnet (Anthropic API) | Best instruction-following, Hindi support | Free credits + pay-as-you-go |
| **Frontend** | React + Tailwind CSS | Fast, component-based, responsive | Free |
| **Voice I/O** | Web Speech API (browser) | Hindi/Kannada recognition (browser native) | Free |
| **Backend** | Python FastAPI | Fast, async, financial calculations | Free |
| **Database** | SQLite (local) / Firebase (cloud) | Simple for hackathon; scalable for prod | Free tier |
| **Earnings Sync** | Swiggy/Zomato API (mocked) | Real APIs exist; mocking for hackathon | Free (mock) |
| **SMS Parsing** | Regex + Claude | No third-party SMS service (expensive); use Claude to parse messy SMS | Minimal |
| **Hosting** | Vercel (frontend) + Render (backend) | Free tier sufficient for demo | Free |
| **Govt Data** | Static JSON + web scrape | PM-KISAN, PMSBY eligibility rules | Free |

---

## 9. Non-Functional Requirements

### Performance
- **API response time:** <2 seconds for earnings lookup, <3 seconds for Claude nudge generation
- **SMS parsing:** Batch process nightly, show results by morning

### Security
- **Data minimalism:** No raw SMS stored; parse & delete
- **Encryption:** Earnings & spending data encrypted at rest (SQLite with sqlcipher)
- **Privacy:** No third-party tracking; no loan referral commissions

### Accessibility
- **Voice-first:** Default to speech input (Web Speech API)
- **Low-data mode:** Works on 3G; minimal payload
- **Languages:** Hindi + Kannada for launch; 8 languages in roadmap

### Ethical Safeguards
- **No dark patterns:** No nudges designed to increase engagement over wellbeing
- **Crisis escalation:** If debt spiral detected, link to NGO helplines (NCCR, ILFS)
- **Bias:** Test income variance thresholds across gender, city-tier, delivery platforms
- **Transparency:** User can see why a recommendation was made ("Based on your earnings trend of...")

---

## 10. Success Metrics (Hackathon)

### Build (Week 1)
- ✅ Working earnings tracker (real or mocked API)
- ✅ SMS parser with 80%+ accuracy
- ✅ Safety buffer calculator with 3+ test cases
- ✅ Claude integration for 2+ nudge types
- ✅ Scheme eligibility matcher for 3 schemes
- ✅ Hindi/Kannada voice input working
- ✅ Live demo with realistic Ramesh data

### Demo
- Show Ramesh's 1-month earnings journey (mock data, realistic)
- Fire an alert (overspend detected)
- Simulate a big purchase (bike)
- Ask a question in Hindi; get answer back
- Show scheme eligibility match

### Judges' Perspective
- **Impact:** "153M people need this" → convincing
- **Technical:** "They built a data pipeline, not a chatbot wrapper" → impressive
- **Ethical:** "They thought about crisis escalation, data minimalism, bias" → thoughtful
- **Presentation:** "Clear demo, Ramesh persona, realistic numbers" → professional

---

## 11. Known Limitations & Roadmap

### Hackathon Scope (v1)
- Swiggy/Zomato API is mocked (hooks ready for production)
- SMS parsing is rule-based + Claude (no third-party SMS API)
- Loan application is link-only (no auto-fill)
- Scheme DB is manual (5 schemes, not 500)
- No multi-user (single Ramesh profile for demo)

### Production Roadmap (Post-Hackathon)
- Real Swiggy/Zomato API integration
- Third-party SMS API (Twilio) for automated SMS capture
- One-tap microfinance application (auto-fill + KYC via e-sign)
- Integrate all 50+ govt schemes
- Multi-user with cloud DB (Firebase/Postgres)
- WhatsApp integration for accessibility
- Scheme auto-apply (partner with microfinance companies)

---

## 12. Definition of Done

For this hackathon, GigShield is **done** when:

1. **Core Loop Works:**
   - Earnings logged (auto-sync or manual)
   - Spending tracked (SMS parsed or manual)
   - Safety buffer calculated & displayed
   - One alert fired & shown to user
   - One scheme matched & shown to user

2. **Claude Integration Works:**
   - At least one conversational query answered in Hindi/Kannada
   - Context-aware (uses user's financial data, not generic)
   - Response generated in user's language

3. **UI/UX Minimal but Functional:**
   - Dashboard showing earnings, spending, safety (no fancy design, just clear)
   - Input form for purchase simulation
   - Chat box for conversational queries
   - Buttons to view schemes/loans

4. **Demo-Ready:**
   - Realistic test data (Ramesh's 30-day journey)
   - No crashes during demo
   - Response times <3 seconds
   - Mobile-responsive (works on phone; that's where Ramesh uses it)

5. **Story Clear:**
   - Proposal document explains problem, solution, ethical thinking
   - Team can articulate why this is NOT a chatbot wrapper
   - Judges understand why Ramesh matters

---

## 13. Code Structure (Overview)

```
gigshield/
├── frontend/
│   ├── components/
│   │   ├── Dashboard.jsx          # Shows earnings, spend, safety
│   │   ├── ChatBox.jsx             # Conversational interface
│   │   ├── PurchaseSimulator.jsx   # Big purchase planning
│   │   ├── SchemeList.jsx          # Matched govt schemes
│   │   └── LoanComparison.jsx      # Microfinance options
│   ├── pages/
│   │   ├── Onboarding.jsx
│   │   ├── Home.jsx
│   │   └── Scheme.jsx
│   └── utils/
│       ├── api.js                  # Backend calls
│       └── format.js               # INR formatting, etc.
│
├── backend/
│   ├── app.py                      # FastAPI app
│   ├── routes/
│   │   ├── earnings.py             # GET /earnings, POST /earnings
│   │   ├── spending.py             # POST /sms, GET /categories
│   │   ├── safety.py               # GET /safety-buffer
│   │   ├── alerts.py               # GET /alerts, POST /alerts
│   │   ├── schemes.py              # GET /schemes-match
│   │   ├── loans.py                # GET /loans
│   │   └── claude.py               # POST /chat (calls Claude API)
│   ├── models/
│   │   ├── earnings.py
│   │   ├── spending.py
│   │   ├── user.py
│   │   └── scheme.py
│   ├── services/
│   │   ├── sms_parser.py           # SMS → categories
│   │   ├── safety_calculator.py    # Financial logic
│   │   ├── scheme_matcher.py       # Profile → schemes
│   │   ├── claude_service.py       # Claude API calls
│   │   └── swiggy_mock.py          # Mock API
│   ├── data/
│   │   ├── schemes.json            # Govt scheme DB
│   │   ├── loans.json              # Microfinance options
│   │   └── sms_patterns.json       # Bank SMS regexes
│   └── db.py                       # SQLite connection
│
├── tests/
│   ├── test_sms_parser.py
│   ├── test_safety_calculator.py
│   └── test_scheme_matcher.py
│
└── data/
    └── ramesh_demo_data.json       # 30 days of mock earnings/spending
```

---

## 14. Appendix: Real Ramesh Data (Mock)

```json
{
  "user": {
    "name": "Ramesh",
    "language": "hindi",
    "platform": "swiggy",
    "mandatory_spend": 12000,
    "household_obligation": 5000
  },
  "earnings_30_days": [
    { "date": "2025-04-05", "amount": 1240, "deliveries": 8 },
    { "date": "2025-04-06", "amount": 980, "deliveries": 6 },
    { "date": "2025-04-07", "amount": 1800, "deliveries": 12 },
    { "date": "2025-04-08", "amount": 450, "deliveries": 3 },
    ...
  ],
  "spending_30_days": [
    { "date": "2025-04-05", "amount": 600, "category": "fuel", "source": "sms" },
    { "date": "2025-04-05", "amount": 200, "category": "food", "source": "manual" },
    { "date": "2025-04-06", "amount": 7000, "category": "rent", "source": "manual" },
    ...
  ],
  "current_savings": 3200,
  "safety_buffer_days": 1.8,
  "recommended_safety": 51420,
  "matched_schemes": [
    {
      "name": "PM-KISAN",
      "eligible": true,
      "amount": 6000,
      "annual": true,
      "link": "https://pmkisan.gov.in"
    },
    {
      "name": "PMSBY",
      "eligible": true,
      "amount": 200000,
      "annual_cost": 20,
      "link": "https://sbi.co.in/pmsby"
    }
  ]
}
```

---

## 15. Key Success Factors for Judging

1. **Problem Clarity:** Peter will ask "Who is this for?" Answer: 153M gig workers, specifically Ramesh.
2. **Solution Fit:** Peter will ask "Why Claude?" Answer: Natural language in Hindi/Kannada, context-aware nudges.
3. **Ethical Depth:** Peter will ask "What could go wrong?" Answer: Crisis escalation, data minimalism, bias testing.
4. **Technical Realism:** Peter will ask "Can you build this in a day?" Answer: Yes, with mocked Swiggy API, realistic demo data.
5. **Demonstration:** Peter will want to see it work: earnings → alert → purchase simulation → scheme match.

---

**End of Product Specification**

---

*Next Step: Hand this to your engineering team with the BUILD_README.md for implementation.*
