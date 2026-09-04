from services.nlp import parse_vernacular_intent


def test_parses_english_business_request():
    parsed = parse_vernacular_intent(
        "I need 1.2 lakh for a tailoring shop. My family income is 150000 rupees.", 26.1, 91.7
    )
    assert parsed.business_type == "Tailoring"
    assert parsed.capital_required == 120000
    assert parsed.annual_income == 150000


def test_parses_hindi_digits_and_intent():
    parsed = parse_vernacular_intent("मुझे सिलाई के लिए १ लाख चाहिए। मेरी आय २ लाख है।", 26.1, 91.7)
    assert parsed.business_type == "Tailoring"
    assert parsed.capital_required == 100000
    assert parsed.annual_income == 200000


def test_parses_green_business_request():
    parsed = parse_vernacular_intent(
        "I need 5 lakh for a solar e-rickshaw business. My annual income is 300000 rupees.", 26.1, 91.7
    )
    assert parsed.business_type == "Green"
