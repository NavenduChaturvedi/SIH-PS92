"""Small, auditable scheme catalogue used by the recommender.

Replace these seeded demo values with the latest official circulars before a
production launch.  Keeping policy values in one place makes that review easy.

Only schemes that are safely auto-selectable from data this app actually
collects (project cost, income, and a business/activity type) live here.
Schemes gated on things we don't ask for — gender (Mahila Adhikarita),
employment category (Swachhta Udyami), or that aren't a conventional EMI
loan at all (VCF-SC venture capital, SCLCSS capital subsidy) — are
deliberately left out of auto-matching; they still exist as reference data
in services/scheme_catalogue.py. Udyam Nidhi Yojana and Laghu Vyavasay
Yojana are also left out even though their cost bracket is easy to detect,
because both cover the same ₹1.4L-5L range as Term Loan through different
channels at very different rates (13-15% vs 6%) — picking one automatically
could steer an applicant to a worse deal than they could actually get.
"""

try:
    from services.scheme_catalogue import get_scheme
except ModuleNotFoundError:
    from .scheme_catalogue import get_scheme

SCHEMES = {
    "Microfinance": {
        "name": "Micro Finance Scheme",
        "max_project_cost": 140000.0,
        "interest_rate": 6.5,
        "moratorium_months": 3,
        "tenure_months": 36,
        "category": "enterprise",
    },
    "Term Loan": {
        "name": "Term Loan Scheme",
        "max_project_cost": 5000000.0,
        "interest_rate": 8.0,
        "moratorium_months": 6,
        "tenure_months": 84,
        "category": "enterprise",
    },
    "Education Loan": {
        "name": "Educational Loan Scheme",
        "max_project_cost": 2000000.0,
        "interest_rate": 7.5,
        "moratorium_months": 6,
        "tenure_months": 84,
        "category": "education",
    },
    "Green Business": {
        "name": "Green Business Scheme (GBS)",
        "max_project_cost": 3000000.0,
        "interest_rate": None,  # tiered — see green_business_interest_rate()
        "moratorium_months": 6,
        "tenure_months": 120,
        "category": "enterprise",
    },
}

INCOME_CEILING = 500000.0
BENEFICIARY_CONTRIBUTION = 0.10


def determine_scheme(business_type: str, education_status: str | None, capital_required: float) -> str:
    """Single source of truth for auto-matching, shared by the simulator
    (which computes terms) and the partner router (which needs the same
    scheme name to filter channel partners) so they can't drift apart."""
    if business_type == "Education" or education_status:
        return "Education Loan"
    if business_type == "Green" and capital_required <= SCHEMES["Green Business"]["max_project_cost"]:
        return "Green Business"
    if capital_required <= SCHEMES["Microfinance"]["max_project_cost"]:
        return "Microfinance"
    return "Term Loan"


def green_business_interest_rate(capital_required: float) -> float:
    tiers = get_scheme("green_business")["interest_rate_tiers"]
    for tier in tiers:
        max_cost = tier.get("max_project_cost")
        if max_cost is None or capital_required <= max_cost:
            return tier["beneficiary_interest_rate"]
    return tiers[-1]["beneficiary_interest_rate"]
