SCHEMES = [
    {
        "name": "PM-KISAN",
        "description": "Annual income support",
        "annual_amount": 6000,
        "annual_cost": 0,
        "link": "https://pmkisan.gov.in",
        "category": "income",
        "eligibility": {"max_annual_income": 200000},
    },
    {
        "name": "PMSBY",
        "description": "Accident insurance cover",
        "annual_amount": 200000,
        "annual_cost": 20,
        "link": "https://sbi.co.in/pmsby",
        "category": "insurance",
        "eligibility": {"min_age": 18, "max_age": 70},
    },
    {
        "name": "PMJJBY",
        "description": "Life insurance cover",
        "annual_amount": 200000,
        "annual_cost": 436,
        "link": "https://sbi.co.in/pmjjby",
        "category": "insurance",
        "eligibility": {"min_age": 18, "max_age": 55},
    },
    {
        "name": "Ujjivan Microloans",
        "description": "Microloans for gig workers",
        "annual_amount": 50000,
        "annual_cost": 18,
        "link": "https://www.ujjivansfb.in",
        "category": "loan",
        "eligibility": {"min_annual_income": 50000, "max_annual_income": 500000},
    },
]


def match_schemes(profile):
    matched = []
    annual_income = profile.get("annual_income", 0)
    age = profile.get("age", 0)

    for scheme in SCHEMES:
        eligibility = scheme.get("eligibility", {})
        eligible = True

        if "min_annual_income" in eligibility and annual_income < eligibility["min_annual_income"]:
            eligible = False
        if "max_annual_income" in eligibility and annual_income > eligibility["max_annual_income"]:
            eligible = False
        if "min_age" in eligibility and age < eligibility["min_age"]:
            eligible = False
        if "max_age" in eligibility and age > eligibility["max_age"]:
            eligible = False

        if eligible:
            matched.append({
                **scheme,
                "eligible": True,
                "action": "Apply at {0}".format(scheme["link"]),
            })

    return matched
