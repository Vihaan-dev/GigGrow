import re

AMOUNT_RE = re.compile(r"(?:INR|Rs\.?|Rs)\s*([0-9,]+(?:\.[0-9]+)?)", re.IGNORECASE)

CATEGORY_KEYWORDS = {
    "fuel": ["petrol", "pump", "fuel", "shell", "hp", "iocl", "bpcl", "essar"],
    "food": ["restaurant", "food", "swiggy", "zomato", "cafe", "coffee", "supermarket"],
    "rent": ["landlord", "rent", "deposit"],
    "transfer": ["transfer", "sent to", "paid to", "imps", "neft", "upi"],
}


def parse_sms(sms_text):
    if not sms_text or not isinstance(sms_text, str):
        return {"error": "sms_text_required"}

    match = AMOUNT_RE.search(sms_text)
    if not match:
        return {"error": "amount_not_found"}

    amount_raw = match.group(1).replace(",", "")
    amount = int(float(amount_raw))

    sms_lower = sms_text.lower()

    if "credit" in sms_lower and ("swiggy" in sms_lower or "zomato" in sms_lower):
        return {
            "amount": amount,
            "category": "income",
            "type": "earning",
            "confidence": 95,
            "notes": "platform_credit",
            "raw_sms": sms_text,
        }

    category = "other"
    confidence = 50

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in sms_lower:
                category = cat
                confidence = 90
                break
        if confidence == 90:
            break

    return {
        "amount": amount,
        "category": category,
        "type": "expense",
        "confidence": confidence,
        "raw_sms": sms_text,
    }
