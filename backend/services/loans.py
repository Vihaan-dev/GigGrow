LOANS = [
    {
        "name": "Ujjivan",
        "apy": 18,
        "min_amount": 5000,
        "max_amount": 50000,
        "min_annual_income": 50000,
        "max_annual_income": 500000,
        "link": "https://www.ujjivansfb.in",
    },
    {
        "name": "Local Moneylender",
        "apy": 60,
        "min_amount": 2000,
        "max_amount": 30000,
        "min_annual_income": 0,
        "max_annual_income": 1000000,
        "link": "https://example.com/moneylender",
    },
    {
        "name": "KGFS",
        "apy": 12,
        "min_amount": 10000,
        "max_amount": 60000,
        "min_annual_income": 40000,
        "max_annual_income": 500000,
        "link": "https://www.kgfs.org",
    },
]


def match_loans(profile, amount=None):
    matched = []
    annual_income = profile.get("annual_income", 0)

    for loan in LOANS:
        if annual_income < loan["min_annual_income"]:
            continue
        if annual_income > loan["max_annual_income"]:
            continue
        if amount is not None:
            if amount < loan["min_amount"] or amount > loan["max_amount"]:
                continue

        matched.append({
            **loan,
            "eligible": True,
        })

    return matched
