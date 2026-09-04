# backend/services/nlp.py
import re

try:
    from schemas import LoanApplicationRequest
except ModuleNotFoundError:
    from ..schemas import LoanApplicationRequest


EDUCATION_KEYWORDS = {
    'education', 'student', 'college', 'school', 'course', 'study',
    'tuition', 'degree', 'engineering', 'medical', 'university',
    'higher education', 'admission', 'semester', 'exam', 'पढ़ाई', 'शिक्षा', 'कॉलेज', 'छात्र', 'स्टूडेंट'
}

BUSINESS_KEYWORDS = {
    'tailor': 'Tailoring',
    'tailoring': 'Tailoring',
    'sewing': 'Tailoring',
    'stitching': 'Tailoring',
    'garment': 'Tailoring',
    'dressmaker': 'Tailoring',
    'farming': 'Farming',
    'farmer': 'Farming',
    'tractor': 'Farming',
    'agriculture': 'Farming',
    'cultivation': 'Farming',
    'field': 'Farming',
    'weld': 'Welding',
    'welding': 'Welding',
    'fabrication': 'Welding',
    'metal': 'Welding',
    'workshop': 'Welding',
    'dairy': 'Dairy',
    'milk': 'Dairy',
    'cattle': 'Dairy',
    'poultry': 'Dairy',
    'cow': 'Dairy',
    'buffalo': 'Dairy',
    'solar': 'Green',
    'e-rickshaw': 'Green',
    'erickshaw': 'Green',
    'e rickshaw': 'Green',
    'poly house': 'Green',
    'polyhouse': 'Green',
    'green business': 'Green',
    'green energy': 'Green',
    'shop': 'General',
    'business': 'General',
    'enterprise': 'General',
    'सिलाई': 'Tailoring',
    'दर्जी': 'Tailoring',
    'खेती': 'Farming',
    'कृषि': 'Farming',
    'डेयरी': 'Dairy',
    'दूध': 'Dairy',
    'वेल्डिंग': 'Welding',
    'सोलर': 'Green',
    'ई-रिक्शा': 'Green',
    'दुकान': 'General',
    'व्यवसाय': 'General',
}

CAPITAL_HINTS = {
    'need', 'need money', 'loan', 'borrow', 'require', 'requires', 'requirement',
    'capital', 'amount', 'project', 'business', 'shop', 'startup'
}

INCOME_HINTS = {
    'income', 'salary', 'earning', 'earns', 'earn', 'annual income',
    'yearly income', 'family income', 'monthly income'
}


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.translate(str.maketrans('०१२३४५६७८९', '0123456789'))
    text = text.replace('₹', ' rupees ')
    text = text.replace('लाख', ' lakh ')
    text = text.replace('हजार', ' thousand ')
    text = text.replace('रुपये', ' rupees ')
    text = re.sub(r'\brs\.?\b', ' rupees ', text)
    text = text.replace(',', '')
    text = text.replace('lac', ' lakh ')
    text = text.replace('lacs', ' lakh ')
    text = text.replace('lakhs', ' lakh ')
    text = text.replace('crores', ' crore ')
    text = text.replace('cr.', ' crore ')
    text = text.replace('cr', ' crore ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _tokenize(text: str):
    normalized = _normalize_text(text)
    return re.findall(r"\d+(?:\.\d+)?|[a-z]+|[\u0900-\u097f]+", normalized)


def _compound_amount_in_text(text: str) -> float:
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*crore\s*(?:and\s+)?(\d+(?:\.\d+)?)\s*lakh', lambda a, b: float(a) * 10000000 + float(b) * 100000),
        (r'(\d+(?:\.\d+)?)\s*lakh\s*(?:and\s+)?(\d+(?:\.\d+)?)\s*thousand', lambda a, b: float(a) * 100000 + float(b) * 1000),
        (r'(\d+(?:\.\d+)?)\s*crore', lambda a: float(a) * 10000000),
        (r'(\d+(?:\.\d+)?)\s*lakh', lambda a: float(a) * 100000),
        (r'(\d+(?:\.\d+)?)\s*thousand', lambda a: float(a) * 1000),
        (r'(\d+(?:\.\d+)?)\s*rupees', lambda a: float(a)),
        (r'(\d+(?:\.\d+)?)', lambda a: float(a)),
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, text)
        if match:
            values = match.groups()
            if len(values) == 2:
                return converter(*values)
            return converter(values[0])
    return 0.0


def _extract_amount(text: str, context_hints=None) -> float:
    text = _normalize_text(text)
    tokens = _tokenize(text)

    if not tokens:
        return 0.0

    if context_hints:
        for hint in context_hints:
            if hint in text:
                return _compound_amount_in_text(text)

    return _compound_amount_in_text(text)


def _detect_business_type(text: str) -> str:
    lowered = _normalize_text(text)
    for keyword, value in BUSINESS_KEYWORDS.items():
        if keyword in lowered:
            return value
    return 'General'


def _detect_education_status(text: str):
    lowered = _normalize_text(text)
    for keyword in EDUCATION_KEYWORDS:
        if keyword in lowered:
            return 'student'
    return None


def _extract_capital(text: str) -> float:
    lowered = _normalize_text(text)

    context_pattern = r'(?:need|need money|borrow|loan|loan amount|require|requires|capital|project|amount|startup|business|चाहिए|ऋण)\s*(?:of|for|is|around|about|का|के लिए)?\s*(?:rupees\s+)?(\d+(?:\.\d+)?\s*(?:lakh|crore|thousand|rupees|rs)?)'
    match = re.search(context_pattern, lowered)
    if match:
        return _compound_amount_in_text(match.group(0))

    return _extract_amount(lowered, context_hints=CAPITAL_HINTS)


def _extract_income(text: str) -> float:
    lowered = _normalize_text(text)
    income_pattern = r'(?:income|salary|earning|earns|annual income|yearly income|family income|monthly income|आय|कमाई)\s*(?:is|of|around|about|है)?\s*(?:rupees\s+)?(\d+(?:\.\d+)?\s*(?:lakh|crore|thousand|rupees|rs)?)'
    match = re.search(income_pattern, lowered)
    if match:
        return _compound_amount_in_text(match.group(0))
    return _extract_amount(lowered, context_hints=INCOME_HINTS)


def parse_vernacular_intent(text: str, lat: float, lon: float) -> LoanApplicationRequest:
    """
    A token-first intent parser for Indian loan text and voice-transcript style input.
    It keeps a lightweight, explainable extraction layer instead of a full ML pipeline,
    while still handling forms like: 30 lakh, 3 lac, 2 crore, 3000000, and mixed phrases.
    """
    cleaned = _normalize_text(text)
    education_status = _detect_education_status(cleaned)
    business_type = 'Education' if education_status else _detect_business_type(cleaned)

    capital_required = _extract_capital(cleaned)
    annual_income = _extract_income(cleaned)

    return LoanApplicationRequest(
        business_type=business_type,
        capital_required=capital_required,
        annual_income=annual_income,
        latitude=lat,
        longitude=lon,
        education_status=education_status,
    )
