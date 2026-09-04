import pytest

from schemas import LoanApplicationRequest
from services.simulator import simulate_loan_terms


@pytest.mark.parametrize(
    ("capital", "income", "expected_scheme"),
    [
        (140000, 500000, "Microfinance"),
        (140001, 500000, "Term Loan"),
    ],
)
def test_enterprise_scheme_boundaries(capital, income, expected_scheme):
    result = simulate_loan_terms(LoanApplicationRequest(capital_required=capital, annual_income=income))
    assert result.is_eligible is True
    assert result.scheme_category == expected_scheme
    assert result.estimated_emi and result.estimated_emi > 0


def test_income_above_ceiling_is_not_eligible():
    result = simulate_loan_terms(LoanApplicationRequest(capital_required=100000, annual_income=500001))
    assert result.is_eligible is False
    assert "₹5.00 lakh" in result.rejection_reason


def test_missing_values_require_follow_up_instead_of_defaults():
    result = simulate_loan_terms(LoanApplicationRequest(capital_required=0, annual_income=0))
    assert result.is_eligible is False
    assert result.missing_fields == ["project cost", "annual family income"]
    assert "tailoring shop" in result.clarification_prompt


def test_education_scheme_has_its_own_terms():
    result = simulate_loan_terms(LoanApplicationRequest(
        business_type="Education", education_status="student", capital_required=200000, annual_income=300000
    ))
    assert result.is_eligible is True
    assert result.scheme_category == "Education Loan"
    assert result.repayment_tenure_months == 84


@pytest.mark.parametrize(
    ("capital", "expected_rate"),
    [
        (500000, 4.0),
        (1000000, 6.0),
        (2500000, 7.0),
    ],
)
def test_green_business_scheme_uses_tiered_interest_rate(capital, expected_rate):
    result = simulate_loan_terms(LoanApplicationRequest(
        business_type="Green", capital_required=capital, annual_income=300000
    ))
    assert result.is_eligible is True
    assert result.scheme_category == "Green Business"
    assert result.interest_rate == expected_rate


def test_green_business_over_its_ceiling_falls_back_to_term_loan():
    # Above Green Business Scheme's 30L ceiling but still within Term Loan's
    # 50L ceiling — falls back to standard Term Loan financing rather than
    # being rejected outright, since that financing is genuinely available.
    result = simulate_loan_terms(LoanApplicationRequest(
        business_type="Green", capital_required=3500000, annual_income=300000
    ))
    assert result.is_eligible is True
    assert result.scheme_category == "Term Loan"


def test_green_business_beyond_term_loan_ceiling_is_rejected():
    result = simulate_loan_terms(LoanApplicationRequest(
        business_type="Green", capital_required=6000000, annual_income=300000
    ))
    assert result.is_eligible is False
    assert "Term Loan Scheme" in result.rejection_reason
