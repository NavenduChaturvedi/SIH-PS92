from math import pow

try:
    from schemas import LoanApplicationRequest, FinancialSimulationResult
except ModuleNotFoundError:
    from ..schemas import LoanApplicationRequest, FinancialSimulationResult

try:
    from services.schemes import SCHEMES, INCOME_CEILING, BENEFICIARY_CONTRIBUTION, determine_scheme, green_business_interest_rate
except ModuleNotFoundError:
    from .schemes import SCHEMES, INCOME_CEILING, BENEFICIARY_CONTRIBUTION, determine_scheme, green_business_interest_rate


def _emi(principal: float, annual_rate: float, months: int) -> float:
    monthly_rate = annual_rate / 1200
    if not monthly_rate:
        return principal / months
    factor = pow(1 + monthly_rate, months)
    return principal * monthly_rate * factor / (factor - 1)


def simulate_loan_terms(request: LoanApplicationRequest) -> FinancialSimulationResult:
    loan_type = (request.loan_type or request.business_type or "General").strip()
    if loan_type == "Education":
        request.business_type = "Education"
        request.education_status = "student"

    missing_fields = []
    if request.capital_required <= 0:
        missing_fields.append("project cost")
    if request.annual_income <= 0:
        missing_fields.append("annual family income")
    if missing_fields:
        details = " and ".join(missing_fields)
        return FinancialSimulationResult(
            is_eligible=False,
            rejection_reason="I could not understand enough information to recommend a scheme.",
            missing_fields=missing_fields,
            clarification_prompt=(
                f"Please enter your {details}. For example: “I need ₹1 lakh for a tailoring shop; "
                "my annual family income is ₹2 lakh.”"
            ),
        )

    if request.annual_income > INCOME_CEILING:
        return FinancialSimulationResult(
            is_eligible=False,
            rejection_reason="Annual income exceeds the ₹5.00 lakh ceiling for SC concessional schemes."
        )

    scheme = determine_scheme(request.business_type, request.education_status, request.capital_required)

    policy = SCHEMES[scheme]
    if request.capital_required > policy["max_project_cost"]:
        return FinancialSimulationResult(
            is_eligible=False,
            rejection_reason=f"Requested project cost exceeds the {policy['name']} limit of ₹{policy['max_project_cost']:,.0f}.",
        )

    loan_amount = request.capital_required * (1 - BENEFICIARY_CONTRIBUTION)
    margin_money = request.capital_required * BENEFICIARY_CONTRIBUTION
    tenure = policy["tenure_months"]
    interest_rate = green_business_interest_rate(request.capital_required) if scheme == "Green Business" else policy["interest_rate"]
    emi = _emi(loan_amount, interest_rate, tenure)
    reasons = [
        f"Annual family income is within the ₹{INCOME_CEILING:,.0f} eligibility ceiling.",
        f"Project cost fits the ₹{policy['max_project_cost']:,.0f} maximum for this scheme.",
        f"A {BENEFICIARY_CONTRIBUTION:.0%} beneficiary contribution is assumed.",
    ]

    return FinancialSimulationResult(
        is_eligible=True,
        scheme_category=scheme,
        scheme_name=policy["name"],
        match_reasons=reasons,
        total_project_cost=request.capital_required,
        concessional_loan_amount=loan_amount,
        beneficiary_margin_money=margin_money,
        interest_rate=interest_rate,
        moratorium_months=policy["moratorium_months"],
        repayment_tenure_months=tenure,
        estimated_emi=round(emi, 2),
        total_payable=round(emi * tenure, 2),
    )
