"""Thin client for Google's Gemini API, used as a real translation backend.

Both services/translation.py (UI text -> target language) and
services/bhashini.py (vernacular request text -> English, ahead of NLP
parsing) fall back to this when their primary provider isn't configured or
fails, since a GEMINI_API_KEY is already provisioned for this project.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def translate_with_gemini(text: str, target_language: str, source_language: str | None = None) -> str | None:
    """Translate text with Gemini. Returns None (never raises) on any failure
    so callers can fall back to another provider or the original text."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not text or not text.strip():
        return None

    source_clause = f" from language code '{source_language}'" if source_language and source_language != "auto" else ""
    prompt = (
        f"Translate the following text{source_clause} to the language with code "
        f"'{target_language}'. Reply with ONLY the translated text and nothing else "
        f"— no quotes, no explanation, no original text.\n\nText: {text}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }).encode("utf-8")
    request = Request(
        f"{GEMINI_ENDPOINT}?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        translated = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return translated or None
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        return None
