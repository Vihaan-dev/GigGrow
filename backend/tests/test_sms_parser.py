from services.sms_parser import parse_sms


def test_parse_fuel_sms():
    out = parse_sms("HDFC: Debit Rs 600 at Sunbeam Petrol Pump", allow_llm=False)
    assert out["amount"] == 600
    assert out["category"] == "fuel"
    assert out["type"] == "expense"
    assert out["confidence"] >= 80


def test_parse_food_sms():
    out = parse_sms("Axis: Debit Rs 320 at Truffles restaurant", allow_llm=False)
    assert out["amount"] == 320
    assert out["category"] == "food"


def test_parse_swiggy_credit_is_income():
    out = parse_sms("Axis: Credit Rs 1240 from Swiggy Technologies", allow_llm=False)
    assert out["category"] == "income"
    assert out["type"] == "earning"


def test_parse_upi_transfer():
    out = parse_sms("ICICI: Rs 250 paid to Karthik via UPI", allow_llm=False)
    assert out["category"] == "transfer"


def test_parse_unknown_merchant_low_confidence():
    out = parse_sms("SBI: Debit Rs 1800 at Acme Wholesale", allow_llm=False)
    assert out["category"] == "other"
    assert out["confidence"] < 80


def test_parse_missing_amount_returns_error():
    out = parse_sms("Hello world, no money here.", allow_llm=False)
    assert "error" in out
