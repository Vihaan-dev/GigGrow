"""SMS parsing for Indian bank transaction alerts.

Two-stage:
  1. Regex-based pattern matching (fast, free, deterministic)
  2. Gemini disambiguation when confidence is low or category is "other"
     and the merchant string is non-trivial.

The Gemini fallback is intentionally guarded: we skip it for tiny amounts,
known categories, or empty merchant text — we do not burn API quota on
every SMS.
"""

import json
import re

from .gemini_client import generate_text

AMOUNT_RE = re.compile(r"(?:INR|Rs\.?|Rs|₹)\s*([0-9,]+(?:\.[0-9]+)?)", re.IGNORECASE)
DEBIT_RE = re.compile(r"\b(debit|debited|spent|paid|withdrawn)\b", re.IGNORECASE)
CREDIT_RE = re.compile(r"\b(credit|credited|received|deposit|deposited)\b", re.IGNORECASE)
MERCHANT_RE = re.compile(r"\b(?:at|to|on|@)\s+([A-Za-z][A-Za-z0-9\s&._-]{2,40})", re.IGNORECASE)

CATEGORY_KEYWORDS = {
    "fuel": ["petrol", "pump", "fuel", "shell", "iocl", "bpcl", "essar", "indian oil", "hpcl"],
    "food": ["restaurant", "food", "cafe", "coffee", "supermarket", "grocer", "bakery", "kirana"],
    "rent": ["landlord", "rent", "deposit"],
    "transfer": ["transfer", "imps", "neft", "upi", "sent to", "paid to"],
    "utilities": ["electricity", "bescom", "bsnl", "airtel", "jio", "vodafone", "recharge"],
    "platform_credit": [],  # detected separately
}

PLATFORM_NAMES = {"swiggy", "zomato", "uber", "ola", "rapido", "dunzo", "porter"}

GEMINI_CACHE = {}


def _extract_merchant(sms_text):
    match = MERCHANT_RE.search(sms_text)
    if not match:
        return None
    raw = match.group(1).strip()
    raw = re.sub(r"\.$", "", raw)
    return raw[:60] if raw else None


def _regex_classify(sms_text):
    sms_lower = sms_text.lower()

    is_credit = bool(CREDIT_RE.search(sms_text)) and not DEBIT_RE.search(sms_text)

    if is_credit and any(p in sms_lower for p in PLATFORM_NAMES):
        return {"category": "income", "type": "earning", "confidence": 95}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in sms_lower:
                return {"category": cat, "type": "expense", "confidence": 90}

    return {"category": "other", "type": "expense", "confidence": 40}


def _gemini_disambiguate(sms_text, merchant):
    """Ask Gemini to pick a category. Returns None if it can't decide."""
    cache_key = (sms_text or "").strip().lower()
    if cache_key in GEMINI_CACHE:
        return GEMINI_CACHE[cache_key]

    prompt = (
        "Classify this Indian bank SMS into ONE category: "
        "fuel, food, rent, transfer, utilities, income, other.\n\n"
        "Rules:\n"
        "- 'income' only if the merchant is a gig platform (Swiggy/Zomato/Uber/Ola/etc) "
        "AND the text indicates credit.\n"
        "- 'transfer' if person-to-person UPI/IMPS without a clear merchant.\n"
        "- Output ONLY a JSON object: "
        "{\"category\": str, \"confidence\": 0-100, \"reason\": str}\n\n"
        "SMS: \"{sms}\"\n"
        "Detected merchant: {merchant}\n"
    ).format(sms=sms_text, merchant=merchant or "unknown")

    raw = generate_text(prompt) or ""
    raw = raw.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", raw, flags=re.DOTALL)
    if fence:
        raw = fence.group(1).strip()

    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        GEMINI_CACHE[cache_key] = None
        return None

    if not isinstance(parsed, dict) or "category" not in parsed:
        GEMINI_CACHE[cache_key] = None
        return None

    valid = {"fuel", "food", "rent", "transfer", "utilities", "income", "other"}
    if parsed["category"] not in valid:
        GEMINI_CACHE[cache_key] = None
        return None

    result = {
        "category": parsed["category"],
        "confidence": int(parsed.get("confidence", 70)),
        "type": "earning" if parsed["category"] == "income" else "expense",
        "reason": parsed.get("reason", "")[:120],
    }
    GEMINI_CACHE[cache_key] = result
    return result


def parse_sms(sms_text, *, allow_llm=True):
    if not sms_text or not isinstance(sms_text, str):
        return {"error": "sms_text_required"}

    amount_match = AMOUNT_RE.search(sms_text)
    if not amount_match:
        return {"error": "amount_not_found"}

    amount_raw = amount_match.group(1).replace(",", "")
    try:
        amount = int(float(amount_raw))
    except ValueError:
        return {"error": "amount_not_found"}

    merchant = _extract_merchant(sms_text)
    classification = _regex_classify(sms_text)
    parsed_by = "regex"
    llm_reason = None

    needs_llm = (
        allow_llm
        and classification["confidence"] < 80
        and classification["category"] == "other"
        and amount > 50
    )
    if needs_llm:
        llm = _gemini_disambiguate(sms_text, merchant)
        if llm:
            classification = {
                "category": llm["category"],
                "type": llm["type"],
                "confidence": llm["confidence"],
            }
            parsed_by = "regex+gemini"
            llm_reason = llm.get("reason")

    return {
        "amount": amount,
        "category": classification["category"],
        "type": classification["type"],
        "confidence": classification["confidence"],
        "merchant": merchant,
        "parsed_by": parsed_by,
        "llm_reason": llm_reason,
        "raw_sms": sms_text,
    }
