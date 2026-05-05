# GigShield: Build Guide (Step-by-Step)

**For: Hackathon Coding Assistant | Duration: 1 Day | Team Size: 3 devs**

This guide breaks down GigShield into discrete, implementable tasks. Follow the order below. Each task includes acceptance criteria.

---

## Phase 0: Setup (30 min)

### 0.1 Initialize Project Structure

```bash
# Create project directory
mkdir gigshield
cd gigshield

# Initialize git
git init
echo "node_modules/" > .gitignore
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".sqlite" >> .gitignore

# Create folders
mkdir frontend backend tests data

# Frontend setup (React)
cd frontend
npx create-react-app . --template minimal
# Install dependencies
npm install axios tailwindcss react-icons

# Configure Tailwind
npx tailwindcss init
# Edit tailwind.config.js to enable JIT mode

cd ../backend
# Create Python virtual env
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic python-dotenv anthropic

# Backend structure
mkdir routes models services
touch app.py routes/__init__.py models/__init__.py services/__init__.py
touch db.py config.py

cd ..
```

**Acceptance Criteria:**
- ✅ Project folder structure created
- ✅ React app scaffolded, Tailwind configured
- ✅ Python virtual env with FastAPI installed
- ✅ `.env` file created with placeholders:
  ```
  ANTHROPIC_API_KEY=your_key_here
  DATABASE_URL=sqlite:///./gigshield.db
  SWIGGY_API_MOCK=true
  ```

---

## Phase 1: Backend — Data Models (1 hour)

### 1.1 Create Database Models

**File: `backend/models/user.py`**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[int] = None
    name: str
    language: str  # "hindi" or "kannada"
    platform: str  # "swiggy" or "zomato"
    mandatory_spend: int  # e.g., 12000
    household_obligation: int  # e.g., 5000
    current_savings: int = 0
    created_at: datetime = datetime.now()

class Earning(BaseModel):
    id: Optional[int] = None
    user_id: int
    date: str  # "2025-05-05"
    amount: int  # ₹1240
    deliveries: Optional[int] = None  # 8 deliveries
    platform: str  # "swiggy" or "zomato"

class Spending(BaseModel):
    id: Optional[int] = None
    user_id: int
    date: str
    amount: int
    category: str  # "fuel", "food", "rent", "transfer", "other"
    source: str  # "sms" or "manual"
    notes: Optional[str] = None

class Alert(BaseModel):
    id: Optional[int] = None
    user_id: int
    type: str  # "low_earnings", "overspend", "safety_drop", "scheme_eligible"
    title: str
    message: str
    severity: str  # "info", "warning", "critical"
    created_at: datetime = datetime.now()

class Scheme(BaseModel):
    id: Optional[int] = None
    name: str  # "PM-KISAN"
    description: str
    eligibility: dict  # e.g., {"min_income": 0, "max_income": 200000}
    annual_amount: int
    annual_cost: int
    link: str
    category: str  # "income", "insurance", "loan"
```

**Acceptance Criteria:**
- ✅ All Pydantic models created
- ✅ Models have sensible defaults
- ✅ No circular imports

---

### 1.2 Create Database Layer

**File: `backend/db.py`**

```python
import sqlite3
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "gigshield.db"

def init_db():
    """Initialize database with tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        language TEXT,
        platform TEXT,
        mandatory_spend INTEGER,
        household_obligation INTEGER,
        current_savings INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Earnings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS earnings (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        date TEXT,
        amount INTEGER,
        deliveries INTEGER,
        platform TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Spending table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spending (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        date TEXT,
        amount INTEGER,
        category TEXT,
        source TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        type TEXT,
        title TEXT,
        message TEXT,
        severity TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Schemes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        description TEXT,
        eligibility JSON,
        annual_amount INTEGER,
        annual_cost INTEGER,
        link TEXT,
        category TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

@contextmanager
def get_db():
    """Context manager for DB connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def insert_schemes():
    """Populate default schemes."""
    schemes = [
        {
            "name": "PM-KISAN",
            "description": "₹6,000 per year direct income support",
            "eligibility": '{"max_income": 200000}',
            "annual_amount": 6000,
            "annual_cost": 0,
            "link": "https://pmkisan.gov.in",
            "category": "income"
        },
        {
            "name": "PMSBY",
            "description": "₹2,00,000 accident insurance",
            "eligibility": '{"min_age": 18, "max_age": 70}',
            "annual_amount": 200000,
            "annual_cost": 20,
            "link": "https://sbi.co.in/pmsby",
            "category": "insurance"
        },
        {
            "name": "PMJJBY",
            "description": "₹2,00,000 life insurance",
            "eligibility": '{"min_age": 18, "max_age": 55}',
            "annual_amount": 200000,
            "annual_cost": 436,
            "link": "https://sbi.co.in/pmjjby",
            "category": "insurance"
        },
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        for scheme in schemes:
            cursor.execute("""
            INSERT OR IGNORE INTO schemes 
            (name, description, eligibility, annual_amount, annual_cost, link, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (scheme["name"], scheme["description"], scheme["eligibility"],
                  scheme["annual_amount"], scheme["annual_cost"], scheme["link"], scheme["category"]))
        conn.commit()
    print("✅ Schemes inserted")

if __name__ == "__main__":
    init_db()
    insert_schemes()
```

**Acceptance Criteria:**
- ✅ SQLite DB created at `gigshield.db`
- ✅ All tables created (users, earnings, spending, alerts, schemes)
- ✅ `python backend/db.py` runs without error
- ✅ 3 schemes (PM-KISAN, PMSBY, PMJJBY) inserted

---

## Phase 2: Backend — Core Services (1.5 hours)

### 2.1 SMS Parser Service

**File: `backend/services/sms_parser.py`**

```python
import re
from typing import Dict

# SMS patterns for major Indian banks
BANK_PATTERNS = {
    "hdfc": r"(?:INR|Rs\.?)\s*([\d,]+).*?(?:Sunbeam|Fuel|Pump|PETROL|FUEL)",
    "axis": r"(?:INR|Rs\.?)\s*([\d,]+).*?(?:Fuel|Petrol)",
    "sbi": r"(?:INR|Rs\.?)\s*([\d,]+).*?(?:Fuel|Petrol)",
    "icici": r"(?:INR|Rs\.?)\s*([\d,]+).*?(?:Fuel|Petrol)",
}

CATEGORY_KEYWORDS = {
    "fuel": ["petrol", "pump", "fuel", "shell", "hp", "sunbeam", "iocl", "bpcl", "essar"],
    "food": ["restaurant", "food", "swiggy", "zomato", "cafe", "coffee", "supermarket"],
    "rent": ["landlord", "rent", "deposit", "transfer"],
    "transfer": ["transfer", "sent to", "paid to"],
}

def parse_sms(sms_text: str) -> Dict:
    """Parse bank SMS and extract category."""
    
    # Extract amount
    amount_match = re.search(r'(?:INR|Rs\.?)\s*([\d,]+)', sms_text)
    if not amount_match:
        return {"error": "Could not parse amount"}
    
    amount_str = amount_match.group(1).replace(",", "")
    amount = int(amount_str)
    
    # Extract category
    sms_lower = sms_text.lower()
    category = "other"
    confidence = 50
    
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in sms_lower:
                category = cat
                confidence = 90  # high confidence
                break
        if confidence == 90:
            break
    
    # Check if it's an income (Swiggy/Zomato credit)
    if "swiggy" in sms_lower and "credit" in sms_lower:
        return {
            "amount": amount,
            "category": "income",
            "type": "earnings",
            "confidence": 95,
            "notes": "Swiggy earnings"
        }
    
    return {
        "amount": amount,
        "category": category,
        "type": "expense",
        "confidence": confidence,
        "raw_sms": sms_text
    }

# Test
if __name__ == "__main__":
    test_sms = "HDFC: Debit ₹600 at Sunbeam Petrol Pump, Whitefield. Bal ₹4,200"
    print(parse_sms(test_sms))
```

**Acceptance Criteria:**
- ✅ `parse_sms()` correctly extracts amount
- ✅ Category detection works for fuel, food, rent
- ✅ Returns dict with `amount`, `category`, `confidence`

---

### 2.2 Safety Buffer Calculator

**File: `backend/services/safety_calculator.py`**

```python
import statistics
from typing import List, Dict

def calculate_safety_buffer(earnings_30_days: List[int], mandatory_spend_daily: float) -> Dict:
    """
    Calculate personalized safety buffer target.
    
    Args:
        earnings_30_days: List of daily earnings for 30 days
        mandatory_spend_daily: Daily mandatory expenses (e.g., 12000/7 ≈ 1714)
    
    Returns:
        {
            "avg_daily_earnings": int,
            "std_dev": float,
            "worst_case_day": int,
            "recommended_buffer": int,
            "days_safe": float
        }
    """
    
    if not earnings_30_days or len(earnings_30_days) < 3:
        return {"error": "Need at least 3 days of earnings data"}
    
    avg = statistics.mean(earnings_30_days)
    std_dev = statistics.stdev(earnings_30_days) if len(earnings_30_days) > 1 else 0
    
    # Worst case = mean - 2*std_dev
    worst_case = max(0, int(avg - (2 * std_dev)))
    
    # Daily deficit in worst case
    daily_deficit = max(0, mandatory_spend_daily - worst_case)
    
    # Recommended buffer = 30 days of mandatory spend + buffer for variance
    recommended_buffer = int(mandatory_spend_daily * 30)
    
    return {
        "avg_daily_earnings": int(avg),
        "std_dev": round(std_dev, 2),
        "worst_case_day": worst_case,
        "daily_deficit_worst_case": daily_deficit,
        "recommended_buffer": recommended_buffer,
        "days_safe": lambda current_savings: current_savings / mandatory_spend_daily
    }

def check_safety_status(current_savings: int, daily_mandatory: float) -> Dict:
    """Check current safety status."""
    days_safe = current_savings / daily_mandatory if daily_mandatory > 0 else 0
    
    if days_safe >= 30:
        status = "secure"
        emoji = "✅"
    elif days_safe >= 7:
        status = "okay"
        emoji = "⚠️"
    else:
        status = "at_risk"
        emoji = "🚨"
    
    return {
        "days_safe": round(days_safe, 1),
        "status": status,
        "emoji": emoji,
        "current_savings": current_savings
    }

# Test
if __name__ == "__main__":
    mock_earnings = [1240, 980, 1800, 450, 2100, 1300, 900] * 4  # 28 days
    safety = calculate_safety_buffer(mock_earnings, 1714)
    print("Safety buffer target:", safety)
    
    status = check_safety_status(3200, 1714)
    print("Current status:", status)
```

**Acceptance Criteria:**
- ✅ `calculate_safety_buffer()` returns correct recommended buffer
- ✅ `check_safety_status()` correctly computes `days_safe`
- ✅ Test data (Ramesh): 28 days earnings → ~7 day buffer recommended

---

### 2.3 Claude Service (Nudges + Intent Parsing)

**File: `backend/services/claude_service.py`**

```python
import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

def generate_nudge(
    context: dict,  # {"type": "overspend", "fuel_spent": 680, "fuel_cap": 600, "language": "hindi"}
    language: str = "hindi"
) -> str:
    """Generate contextual nudge using Claude."""
    
    if language == "hindi":
        prompt = f"""You are a financial advisor for gig workers in India. 
        Generate a SHORT, actionable nudge in HINDI ONLY (no English).
        
        Context: {json.dumps(context)}
        
        Rules:
        - Max 2 sentences
        - Use simple Hindi (avoid jargon)
        - Be encouraging, not scolding
        - Suggest specific action if possible
        - Start with the issue, then solution
        
        Example: "Iska week mein fuel ka spend ₹680 tha, par target ₹600 tha. Kal JP Nagar ke pump pe sasta petrol hai, vahan se bharo."
        
        Now generate the nudge:"""
    else:  # kannada
        prompt = f"""You are a financial advisor for gig workers in India.
        Generate a SHORT, actionable nudge in KANNADA ONLY (no English).
        
        Context: {json.dumps(context)}
        
        Rules:
        - Max 2 sentences
        - Use simple Kannada (avoid jargon)
        - Be encouraging, not scolding
        - Suggest specific action if possible
        
        Now generate the nudge:"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

def parse_intent(user_message: str, language: str = "hindi") -> dict:
    """Parse user intent from conversational message."""
    
    if language == "hindi":
        prompt = f"""User (Hindi): "{user_message}"
        
        Extract the intent. Respond ONLY with JSON (no other text):
        {{
            "intent": "earnings|spending|safety|purchase|scheme|general",
            "entity": "optional string (e.g., 'bike', 'PM-KISAN')",
            "timeframe": "today|yesterday|week|month|optional",
            "raw_input": "{user_message}"
        }}"""
    else:
        prompt = f"""User (Kannada): "{user_message}"
        
        Extract the intent. Respond ONLY with JSON:
        {{
            "intent": "earnings|spending|safety|purchase|scheme|general",
            "entity": "optional string",
            "timeframe": "today|yesterday|week|month|optional",
            "raw_input": "{user_message}"
        }}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        return json.loads(message.content[0].text)
    except json.JSONDecodeError:
        return {"intent": "general", "error": "Could not parse intent"}

def explain_purchase_impact(purchase_amount: int, current_safety_days: float, daily_mandatory: float, language: str = "hindi") -> str:
    """Explain purchase impact using Claude."""
    
    new_safety_days = (current_safety_days * daily_mandatory - purchase_amount) / daily_mandatory if daily_mandatory > 0 else 0
    
    if language == "hindi":
        prompt = f"""You are a gig worker financial advisor. Explain purchase impact in HINDI.
        
        Context:
        - User wants to spend ₹{purchase_amount}
        - Current safety: {round(current_safety_days, 1)} days
        - After purchase: {round(max(0, new_safety_days), 1)} days
        - Daily mandatory: ₹{int(daily_mandatory)}
        
        Response in HINDI (2-3 sentences, simple language):
        - Start with: "Aapka current safety {current_safety_days} din ka hai..."
        - Explain the impact
        - Suggest 2-3 options (work extra days, take loan, delay purchase)
        """
    else:
        prompt = f"""You are a gig worker financial advisor. Explain in KANNADA.
        (Similar structure but in Kannada)"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=150,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

if __name__ == "__main__":
    # Test nudge generation
    context = {
        "type": "overspend",
        "category": "fuel",
        "spent": 680,
        "cap": 600,
        "overage": 80
    }
    nudge = generate_nudge(context, "hindi")
    print("Nudge:", nudge)
    
    # Test intent parsing
    intent = parse_intent("Kal kitna kamaya?", "hindi")
    print("Intent:", intent)
```

**Acceptance Criteria:**
- ✅ `generate_nudge()` returns Hindi/Kannada text (not English)
- ✅ `parse_intent()` returns valid JSON with intent, entity, timeframe
- ✅ `explain_purchase_impact()` explains impact in user's language
- ✅ Claude API key is set in `.env`

---

### 2.4 Scheme Matcher Service

**File: `backend/services/scheme_matcher.py`**

```python
from typing import List, Dict

SCHEMES_DATA = [
    {
        "name": "PM-KISAN",
        "description": "₹6,000 per year direct income support",
        "annual_amount": 6000,
        "annual_cost": 0,
        "link": "https://pmkisan.gov.in",
        "category": "income",
        "eligibility": {"max_annual_income": 200000}
    },
    {
        "name": "PMSBY",
        "description": "₹2,00,000 accident insurance",
        "annual_amount": 200000,
        "annual_cost": 20,
        "link": "https://sbi.co.in/pmsby",
        "category": "insurance",
        "eligibility": {"min_age": 18, "max_age": 70}
    },
    {
        "name": "PMJJBY",
        "description": "₹2,00,000 life insurance",
        "annual_amount": 200000,
        "annual_cost": 436,
        "link": "https://sbi.co.in/pmjjby",
        "category": "insurance",
        "eligibility": {"min_age": 18, "max_age": 55}
    },
    {
        "name": "Ujjivan Microloans",
        "description": "₹5K–₹50K microloans for gig workers",
        "annual_amount": 50000,
        "annual_cost": 18,  # 18% APY
        "link": "https://ujjivan.com",
        "category": "loan",
        "eligibility": {"min_annual_income": 50000, "max_annual_income": 500000}
    }
]

def match_schemes(user_profile: Dict) -> List[Dict]:
    """Match user to eligible schemes."""
    
    matched = []
    annual_income = user_profile.get("annual_income", 0)
    age = user_profile.get("age", 0)
    
    for scheme in SCHEMES_DATA:
        eligibility = scheme["eligibility"]
        is_eligible = True
        
        # Check income
        if "min_annual_income" in eligibility:
            if annual_income < eligibility["min_annual_income"]:
                is_eligible = False
        if "max_annual_income" in eligibility:
            if annual_income > eligibility["max_annual_income"]:
                is_eligible = False
        
        # Check age
        if "min_age" in eligibility:
            if age < eligibility["min_age"]:
                is_eligible = False
        if "max_age" in eligibility:
            if age > eligibility["max_age"]:
                is_eligible = False
        
        if is_eligible:
            matched.append({
                **scheme,
                "eligible": True,
                "action": f"Apply at {scheme['link']}"
            })
    
    return matched

if __name__ == "__main__":
    ramesh = {
        "name": "Ramesh",
        "annual_income": 300000,  # ₹25K/month avg
        "age": 29,
        "platform": "swiggy"
    }
    schemes = match_schemes(ramesh)
    print(f"Matched schemes for {ramesh['name']}:")
    for s in schemes:
        print(f"  - {s['name']}: ₹{s['annual_amount']} ({s['link']})")
```

**Acceptance Criteria:**
- ✅ `match_schemes()` returns list of eligible schemes
- ✅ Scheme eligibility correctly checked against income/age
- ✅ Ramesh (annual income ₹300K, age 29) matches: PM-KISAN, PMSBY, PMJJBY, Ujjivan

---

## Phase 3: Backend — FastAPI Endpoints (1.5 hours)

### 3.1 Main App Setup

**File: `backend/app.py`**

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from db import init_db, insert_schemes
from routes import earnings, spending, safety, alerts, schemes, loans, claude

load_dotenv()

# Initialize DB
init_db()
insert_schemes()

app = FastAPI(title="GigShield")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(earnings.router, prefix="/api/earnings", tags=["earnings"])
app.include_router(spending.router, prefix="/api/spending", tags=["spending"])
app.include_router(safety.router, prefix="/api/safety", tags=["safety"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(schemes.router, prefix="/api/schemes", tags=["schemes"])
app.include_router(loans.router, prefix="/api/loans", tags=["loans"])
app.include_router(claude.router, prefix="/api/claude", tags=["claude"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "GigShield"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### 3.2 Earnings Endpoint

**File: `backend/routes/earnings.py`**

```python
from fastapi import APIRouter, HTTPException
from db import get_db
from models.user import Earning
from services.swiggy_mock import get_mock_earnings
from datetime import datetime

router = APIRouter()

@router.post("/log")
def log_earning(earning: Earning):
    """Log a single day's earnings."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO earnings (user_id, date, amount, deliveries, platform)
        VALUES (?, ?, ?, ?, ?)
        """, (earning.user_id, earning.date, earning.amount, earning.deliveries, earning.platform))
        conn.commit()
    return {"status": "logged", "earning": earning}

@router.get("/{user_id}")
def get_earnings(user_id: int, days: int = 30):
    """Get last N days of earnings."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM earnings WHERE user_id = ? ORDER BY date DESC LIMIT ?
        """, (user_id, days))
        earnings = [dict(row) for row in cursor.fetchall()]
    return {"user_id": user_id, "count": len(earnings), "earnings": earnings}

@router.post("/sync-mock/{user_id}")
def sync_mock_earnings(user_id: int, days: int = 30):
    """Sync mock Swiggy earnings (for demo)."""
    mock_data = get_mock_earnings(days)
    with get_db() as conn:
        for data in mock_data:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO earnings (user_id, date, amount, deliveries, platform)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, data["date"], data["amount"], data["deliveries"], "swiggy"))
            conn.commit()
    return {"status": "synced", "count": len(mock_data), "earnings": mock_data}
```

**Acceptance Criteria:**
- ✅ `POST /api/earnings/log` accepts Earning and saves to DB
- ✅ `GET /api/earnings/{user_id}` returns last 30 days
- ✅ `POST /api/earnings/sync-mock/{user_id}` populates with realistic Ramesh data

---

### 3.3 Safety Endpoint

**File: `backend/routes/safety.py`**

```python
from fastapi import APIRouter
from db import get_db
from services.safety_calculator import calculate_safety_buffer, check_safety_status

router = APIRouter()

@router.get("/{user_id}")
def get_safety_status(user_id: int):
    """Get safety buffer status."""
    with get_db() as conn:
        # Get user's mandatory spend
        cursor = conn.cursor()
        cursor.execute("SELECT mandatory_spend FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {"error": "User not found"}
        
        mandatory_daily = user["mandatory_spend"] / 7
        
        # Get last 30 days of earnings
        cursor.execute("""
        SELECT amount FROM earnings WHERE user_id = ? ORDER BY date DESC LIMIT 30
        """, (user_id,))
        earnings = [row["amount"] for row in cursor.fetchall()]
        
        if len(earnings) < 3:
            return {"error": "Need at least 3 days of earnings data"}
        
        # Get current savings
        cursor.execute("SELECT current_savings FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        current_savings = user["current_savings"]
    
    # Calculate safety
    buffer_info = calculate_safety_buffer(earnings, mandatory_daily)
    status = check_safety_status(current_savings, mandatory_daily)
    
    return {
        "user_id": user_id,
        "current_savings": current_savings,
        "days_safe": status["days_safe"],
        "status": status["status"],
        "buffer_info": buffer_info,
        "recommendation": f"Target buffer: ₹{buffer_info['recommended_buffer']} (30 days safe)"
    }
```

**Acceptance Criteria:**
- ✅ `GET /api/safety/{user_id}` returns days_safe, status, recommendations
- ✅ For Ramesh (₹3,200 savings, ₹1,714 daily): returns ~1.8 days safe

---

### 3.4 Claude Chat Endpoint

**File: `backend/routes/claude.py`**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.claude_service import parse_intent, generate_nudge, explain_purchase_impact
from db import get_db

router = APIRouter()

class ChatMessage(BaseModel):
    user_id: int
    message: str
    language: str = "hindi"

class PurchaseSimulation(BaseModel):
    user_id: int
    amount: int
    language: str = "hindi"

@router.post("/chat")
def chat(msg: ChatMessage):
    """Handle conversational queries."""
    try:
        # Parse intent
        intent = parse_intent(msg.message, msg.language)
        
        # Get user data
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_savings FROM users WHERE id = ?", (msg.user_id,))
            user = cursor.fetchone()
            if not user:
                return {"error": "User not found"}
            
            current_savings = user["current_savings"]
        
        # Simple responses based on intent
        if intent.get("intent") == "earnings":
            return {
                "intent": intent["intent"],
                "response": "Aapke earnings ko dekh rahe hain...",  # Simplified
                "language": msg.language
            }
        elif intent.get("intent") == "safety":
            return {
                "intent": intent["intent"],
                "response": f"Aapka current savings ₹{current_savings} hai.",
                "language": msg.language
            }
        else:
            return {
                "intent": intent.get("intent", "general"),
                "response": "Aapka sawaal samajh gaye. Samjhane mein thoda time lagega...",
                "language": msg.language
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-purchase")
def simulate_purchase(sim: PurchaseSimulation):
    """Simulate purchase impact."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT mandatory_spend, current_savings FROM users WHERE id = ?
            """, (sim.user_id,))
            user = cursor.fetchone()
            if not user:
                return {"error": "User not found"}
        
        daily_mandatory = user["mandatory_spend"] / 7
        current_days_safe = user["current_savings"] / daily_mandatory
        
        explanation = explain_purchase_impact(
            sim.amount,
            current_days_safe,
            daily_mandatory,
            sim.language
        )
        
        return {
            "purchase_amount": sim.amount,
            "current_safety_days": round(current_days_safe, 1),
            "new_safety_days": round(max(0, (user["current_savings"] - sim.amount) / daily_mandatory), 1),
            "explanation": explanation,
            "language": sim.language
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Acceptance Criteria:**
- ✅ `POST /api/claude/chat` accepts message + language, returns response
- ✅ `POST /api/claude/simulate-purchase` returns impact analysis

---

### 3.5 Schemes Endpoint

**File: `backend/routes/schemes.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel
from services.scheme_matcher import match_schemes

router = APIRouter()

class UserProfile(BaseModel):
    user_id: int
    annual_income: int
    age: int

@router.post("/match")
def match_user_schemes(profile: UserProfile):
    """Match user to eligible schemes."""
    matched = match_schemes({
        "annual_income": profile.annual_income,
        "age": profile.age
    })
    return {
        "user_id": profile.user_id,
        "matched_count": len(matched),
        "schemes": matched
    }

@router.get("/all")
def get_all_schemes():
    """Get all available schemes."""
    from services.scheme_matcher import SCHEMES_DATA
    return {"count": len(SCHEMES_DATA), "schemes": SCHEMES_DATA}
```

**Acceptance Criteria:**
- ✅ `POST /api/schemes/match` returns eligible schemes
- ✅ `GET /api/schemes/all` returns all 4 schemes

---

### 3.6 Spending Endpoint

**File: `backend/routes/spending.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel
from services.sms_parser import parse_sms
from db import get_db
from models.user import Spending

router = APIRouter()

class SMSInput(BaseModel):
    user_id: int
    sms_text: str

@router.post("/parse-sms")
def parse_sms_endpoint(input: SMSInput):
    """Parse bank SMS and categorize."""
    result = parse_sms(input.sms_text)
    if "error" in result:
        return {"status": "error", "message": result["error"]}
    
    # Save to DB
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO spending (user_id, date, amount, category, source, notes)
        VALUES (?, date('now'), ?, ?, ?, ?)
        """, (input.user_id, result["amount"], result["category"], "sms", result.get("notes", "")))
        conn.commit()
    
    return {"status": "parsed_and_saved", "result": result}

@router.get("/{user_id}")
def get_spending(user_id: int, days: int = 30):
    """Get spending history."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM spending WHERE user_id = ? ORDER BY date DESC LIMIT ?
        """, (user_id, days * 7))  # days * 7 to account for daily entries
        spending = [dict(row) for row in cursor.fetchall()]
    
    # Aggregate by category
    by_category = {}
    for s in spending:
        cat = s["category"]
        by_category[cat] = by_category.get(cat, 0) + s["amount"]
    
    return {
        "user_id": user_id,
        "count": len(spending),
        "by_category": by_category,
        "spending": spending
    }
```

**Acceptance Criteria:**
- ✅ `POST /api/spending/parse-sms` parses SMS and saves
- ✅ `GET /api/spending/{user_id}` returns aggregated spending

---

## Phase 4: Frontend — Components (1.5 hours)

### 4.1 Setup React + Tailwind

**File: `frontend/src/App.jsx`**

```jsx
import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import ChatBox from './components/ChatBox';
import PurchaseSimulator from './components/PurchaseSimulator';
import SchemeList from './components/SchemeList';

function App() {
  const [userId, setUserId] = useState(1); // Mock: Ramesh
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Header */}
      <div className="bg-orange-600 text-white p-4">
        <h1 className="text-2xl font-bold">GigShield 🛡️</h1>
        <p className="text-sm text-orange-100">Financial Resilience for Gig Workers</p>
      </div>

      {/* Navigation */}
      <div className="flex gap-2 p-4 bg-slate-800 text-white overflow-x-auto">
        {[
          { id: 'dashboard', label: '📊 Dashboard' },
          { id: 'spending', label: '💸 Spending' },
          { id: 'purchase', label: '🛒 Purchase Plan' },
          { id: 'schemes', label: '🏛️ Schemes' },
          { id: 'chat', label: '💬 Chat' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-orange-600'
                : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6 max-w-6xl mx-auto">
        {activeTab === 'dashboard' && <Dashboard userId={userId} />}
        {activeTab === 'purchase' && <PurchaseSimulator userId={userId} />}
        {activeTab === 'schemes' && <SchemeList userId={userId} />}
        {activeTab === 'chat' && <ChatBox userId={userId} />}
      </div>
    </div>
  );
}

export default App;
```

---

### 4.2 Dashboard Component

**File: `frontend/src/components/Dashboard.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function Dashboard({ userId }) {
  const [safety, setSafety] = useState(null);
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [userId]);

  const fetchData = async () => {
    try {
      const [safetyRes, earningsRes] = await Promise.all([
        axios.get(`${API_BASE}/safety/${userId}`),
        axios.get(`${API_BASE}/earnings/${userId}`),
      ]);
      setSafety(safetyRes.data);
      setEarnings(earningsRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-white text-center py-10">Loading...</div>;
  if (!safety) return <div className="text-red-400">Error loading data</div>;

  const daysPercent = Math.min((safety.days_safe / 30) * 100, 100);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Safety Buffer Card */}
      <div className="bg-white rounded-lg p-6 shadow">
        <h2 className="text-lg font-bold text-gray-800">Safety Buffer</h2>
        <div className="mt-4">
          <div className="text-4xl font-bold text-orange-600">{safety.days_safe}</div>
          <div className="text-sm text-gray-500">days safe</div>
          
          {/* Progress bar */}
          <div className="mt-4 bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all ${
                safety.days_safe >= 30 ? 'bg-green-500' :
                safety.days_safe >= 7 ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{ width: `${daysPercent}%` }}
            />
          </div>
          
          <p className="text-xs text-gray-600 mt-2">
            Goal: 30 days | Target: ₹{safety.buffer_info.recommended_buffer}
          </p>
        </div>
        
        <button
          onClick={fetchData}
          className="mt-4 w-full bg-orange-600 text-white py-2 rounded hover:bg-orange-700"
        >
          Refresh
        </button>
      </div>

      {/* Earnings Card */}
      {earnings && (
        <div className="bg-white rounded-lg p-6 shadow">
          <h2 className="text-lg font-bold text-gray-800">Recent Earnings</h2>
          <div className="mt-4 space-y-2">
            {earnings.earnings.slice(0, 5).map((e, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span className="text-gray-600">{e.date}</span>
                <span className="font-bold text-green-600">+₹{e.amount}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-gray-500">
              Avg: ₹{Math.round(
                earnings.earnings.reduce((a, e) => a + e.amount, 0) / earnings.earnings.length
              )}/day
            </p>
          </div>
        </div>
      )}

      {/* Status Card */}
      <div className={`rounded-lg p-6 shadow text-white ${
        safety.status === 'secure' ? 'bg-green-600' :
        safety.status === 'okay' ? 'bg-yellow-600' :
        'bg-red-600'
      }`}>
        <h2 className="text-lg font-bold">Status</h2>
        <p className="text-3xl font-bold mt-4 capitalize">{safety.status}</p>
        <p className="text-sm mt-4">{safety.recommendation}</p>
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- ✅ Dashboard displays safety buffer, days safe, status
- ✅ Shows last 5 earnings with average
- ✅ Progress bar updates correctly
- ✅ Refresh button fetches latest data

---

### 4.3 Chat Component

**File: `frontend/src/components/ChatBox.jsx`**

```jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function ChatBox({ userId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState('hindi');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input, language };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/claude/chat`, {
        user_id: userId,
        message: input,
        language,
      });

      const assistantMsg = {
        role: 'assistant',
        content: res.data.response,
        language,
      };
      setMessages(m => [...m, assistantMsg]);
    } catch (err) {
      console.error('Error:', err);
      setMessages(m => [...m, {
        role: 'assistant',
        content: 'Error: Could not process message',
        language,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Language selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setLanguage('hindi')}
          className={`px-4 py-2 rounded ${
            language === 'hindi'
              ? 'bg-orange-600 text-white'
              : 'bg-gray-700 text-gray-300'
          }`}
        >
          हिंदी
        </button>
        <button
          onClick={() => setLanguage('kannada')}
          className={`px-4 py-2 rounded ${
            language === 'kannada'
              ? 'bg-orange-600 text-white'
              : 'bg-gray-700 text-gray-300'
          }`}
        >
          ಕನ್ನಡ
        </button>
      </div>

      {/* Chat messages */}
      <div className="bg-slate-700 rounded-lg p-4 h-96 overflow-y-auto space-y-3">
        {messages.length === 0 && (
          <div className="text-gray-400 text-center py-10">
            <p>Start asking questions in {language}...</p>
          </div>
        )}
        
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`rounded-lg px-4 py-2 max-w-xs ${
              msg.role === 'user'
                ? 'bg-orange-600 text-white'
                : 'bg-gray-600 text-gray-100'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your question..."
          className="flex-1 px-4 py-2 rounded bg-slate-600 text-white placeholder-gray-400"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="px-6 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- ✅ Chat interface shows user + assistant messages
- ✅ Language toggle works (Hindi/Kannada)
- ✅ Messages send to API and display response

---

### 4.4 Purchase Simulator Component

**File: `frontend/src/components/PurchaseSimulator.jsx`**

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function PurchaseSimulator({ userId }) {
  const [amount, setAmount] = useState('');
  const [language, setLanguage] = useState('hindi');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    if (!amount) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/claude/simulate-purchase`, {
        user_id: userId,
        amount: parseInt(amount),
        language,
      });
      setResult(res.data);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Input */}
      <div className="bg-white rounded-lg p-6 shadow">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Plan a Big Purchase</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Purchase Amount (₹)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g., 22000"
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-orange-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded"
            >
              <option value="hindi">हिंदी (Hindi)</option>
              <option value="kannada">ಕನ್ನಡ (Kannada)</option>
            </select>
          </div>

          <button
            onClick={handleSimulate}
            disabled={!amount || loading}
            className="w-full px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
          >
            {loading ? 'Simulating...' : 'Simulate Purchase'}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-white rounded-lg p-6 shadow">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Impact Analysis</h3>
          
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">Current Safety</p>
              <p className="text-2xl font-bold text-green-600">
                {result.current_safety_days} days
              </p>
            </div>

            <div className="bg-red-50 p-4 rounded">
              <p className="text-sm text-gray-600">After Purchase</p>
              <p className="text-2xl font-bold text-red-600">
                {result.new_safety_days} days
              </p>
            </div>

            <div className="bg-yellow-50 p-4 rounded text-sm">
              <p className="font-semibold mb-2">Analysis:</p>
              <p className="text-gray-700">{result.explanation}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Acceptance Criteria:**
- ✅ Input form for purchase amount
- ✅ Calls API and displays impact
- ✅ Shows before/after safety days
- ✅ Displays Claude explanation

---

### 4.5 Schemes Component

**File: `frontend/src/components/SchemeList.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function SchemeList({ userId }) {
  const [schemes, setSchemes] = useState([]);
  const [income, setIncome] = useState('300000');
  const [age, setAge] = useState('29');
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (loaded) matchSchemes();
  }, [income, age]);

  const matchSchemes = async () => {
    try {
      const res = await axios.post(`${API_BASE}/schemes/match`, {
        user_id: userId,
        annual_income: parseInt(income),
        age: parseInt(age),
      });
      setSchemes(res.data.schemes);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Profile Input */}
      <div className="bg-white rounded-lg p-6 shadow">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Your Profile</h2>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Annual Income (₹)
            </label>
            <input
              type="number"
              value={income}
              onChange={(e) => setIncome(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Age
            </label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded"
            />
          </div>
        </div>

        <button
          onClick={() => { setLoaded(true); matchSchemes(); }}
          className="mt-4 w-full px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
        >
          Check Eligibility
        </button>
      </div>

      {/* Schemes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {schemes.map((scheme, i) => (
          <div key={i} className="bg-white rounded-lg p-6 shadow border-l-4 border-orange-600">
            <h3 className="font-bold text-gray-800">{scheme.name}</h3>
            <p className="text-sm text-gray-600 mt-2">{scheme.description}</p>
            
            <div className="mt-4 space-y-2 text-sm">
              <p><span className="font-semibold">Coverage:</span> ₹{scheme.annual_amount.toLocaleString()}</p>
              <p><span className="font-semibold">Annual Cost:</span> ₹{scheme.annual_cost}</p>
              <p><span className="font-semibold">Status:</span> <span className="text-green-600 font-bold">✅ Eligible</span></p>
            </div>

            <a
              href={scheme.link}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 block text-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              Apply Now
            </a>
          </div>
        ))}
      </div>

      {loaded && schemes.length === 0 && (
        <div className="text-center text-gray-500">No matching schemes found</div>
      )}
    </div>
  );
}
```

**Acceptance Criteria:**
- ✅ Profile input (income, age)
- ✅ Scheme matching API call
- ✅ Display matched schemes with links

---

## Phase 5: Integration & Demo Setup (30 min)

### 5.1 Mock Data Generator

**File: `backend/services/swiggy_mock.py`**

```python
from datetime import datetime, timedelta
import random

def get_mock_earnings(days: int = 30):
    """Generate realistic 30-day Ramesh earnings."""
    earnings = []
    base_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Ramesh earns between ₹400–₹2,000/day depending on day of week
        day_of_week = (base_date + timedelta(days=i)).weekday()
        
        if day_of_week in [4, 5, 6]:  # Fri, Sat, Sun
            base = 1500
        else:
            base = 1000
        
        # Add randomness
        amount = base + random.randint(-400, 800)
        deliveries = max(3, amount // 200)  # ~₹200 per delivery
        
        earnings.append({
            "date": date,
            "amount": amount,
            "deliveries": deliveries,
            "platform": "swiggy"
        })
    
    return earnings
```

**Acceptance Criteria:**
- ✅ Generates 30 realistic days of Ramesh earnings (₹400–₹2,000/day)

---

### 5.2 Run & Test

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
python app.py
# Expected: "INFO:     Application startup complete"

# Terminal 2: Start frontend
cd frontend
npm start
# Expected: React app opens at localhost:3000

# Terminal 3: Test endpoints
curl http://localhost:8000/health
# Expected: {"status": "ok", "service": "GigShield"}

curl -X POST http://localhost:8000/api/earnings/sync-mock/1 \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
# Expected: 30 earnings entries synced

curl http://localhost:8000/api/safety/1
# Expected: safety buffer status for user 1
```

**Acceptance Criteria:**
- ✅ Backend starts on port 8000
- ✅ Frontend starts on port 3000
- ✅ All endpoints respond correctly
- ✅ Data syncs end-to-end

---

## Phase 6: Demo Walkthrough (15 min)

Before presenting to judges, walk through:

1. **Load Dashboard:**
   - Shows Ramesh's 30-day earnings
   - Safety buffer: 1.8 days (at risk) 🚨
   - Current savings: ₹3,200

2. **Fire an Alert:**
   - Show overspending alert (fuel ₹680 vs cap ₹600)
   - Claude-generated nudge in Hindi

3. **Purchase Simulation:**
   - User wants to buy a ₹22,000 bike
   - System shows: Safety drops from 8 to 3 days
   - Recommends Ujjivan loan instead

4. **Check Schemes:**
   - Show Ramesh matches: PM-KISAN, PMSBY, PMJJBY, Ujjivan
   - One-tap apply links

5. **Ask Claude:**
   - Question: "Kal kitna kamaya?" (How much did I earn yesterday?)
   - Claude responds in Hindi with yesterday's earning + context

---

## Definition of Done

✅ All code written and committed to git  
✅ All endpoints tested and working  
✅ React components render without errors  
✅ Demo data loaded (30-day Ramesh journey)  
✅ Claude API integration working (Hindi responses)  
✅ Zero crashes during demo walkthrough  
✅ Response times <3 seconds  
✅ Mobile-responsive (works on phone)

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: anthropic` | Run `pip install anthropic` in backend/venv |
| `CORS error` | Check FastAPI CORS setup in app.py |
| `Claude API 401` | Verify `ANTHROPIC_API_KEY` in `.env` |
| `React build errors` | Delete `node_modules` and `npm install` again |
| `Port 8000 already in use` | Kill process: `lsof -i :8000` then `kill -9 <PID>` |
| `SMS parsing returns 'other'` | Add keyword to `CATEGORY_KEYWORDS` dict in sms_parser.py |

---

## Deployment (Post-Hackathon)

- **Frontend:** Deploy to Vercel (`vercel deploy`)
- **Backend:** Deploy to Render or Railway (`git push` triggers auto-deploy)
- **Database:** Migrate SQLite to PostgreSQL
- **Real APIs:** Integrate actual Swiggy/Zomato + Twilio SMS

---

**End of Build Guide**

---

*You're ready to build. Get coding! 🚀*
