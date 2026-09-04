"""Boundary for BHASHINI translation services.

The BHASHINI pipeline and authentication payload are provisioned per account.
This adapter expects a tiny server-side gateway that normalizes that provider
payload to {text, source_language, target_language} -> {translated_text}.
Keeping keys and provider-specific request shapes here prevents exposing them
to the Vue application and leaves the matching engine provider-independent.
"""

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from services.gemini import translate_with_gemini
except ModuleNotFoundError:
    from .gemini import translate_with_gemini


def _translate_via_bhashini_gateway(text: str, source_language: str) -> str | None:
    gateway_url = os.getenv("BHASHINI_GATEWAY_URL")
    api_key = os.getenv("BHASHINI_API_KEY")
    if not gateway_url or not api_key:
        return None

    payload = json.dumps({
        "text": text,
        "source_language": source_language,
        "target_language": "en",
    }).encode("utf-8")
    request = Request(
        gateway_url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        translated = data.get("translated_text")
        return translated if isinstance(translated, str) and translated.strip() else None
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def translate_to_english(text: str, source_language: str) -> tuple[str, str]:
    """Normalize vernacular request text to English before NLP parsing.

    Tries the BHASHINI gateway first (the government-provisioned pipeline
    this project is built around), then falls back to Gemini if that isn't
    configured or fails, and finally passes the text through untouched so the
    keyword-based Hindi/English parser in services/nlp.py still has a shot.
    """
    if not text or not text.strip() or source_language in {"en", "en-IN"}:
        return text, "local"

    bhashini_result = _translate_via_bhashini_gateway(text, source_language)
    if bhashini_result:
        return bhashini_result, "bhashini"

    gemini_result = translate_with_gemini(text, target_language="en", source_language=source_language)
    if gemini_result:
        return gemini_result, "gemini"

    return text, "local"
