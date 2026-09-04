import json
import os
import html
import urllib.parse
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

try:
    from services.gemini import translate_with_gemini
except ModuleNotFoundError:
    from .gemini import translate_with_gemini

SUPPORTED_TRANSLATION_LANGUAGES = {
    "en", "as", "bn", "doi", "gu", "hi", "kn", "kok", "mai", "ml",
    "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur"
}

def translate_text(text: str, target_language: str = "en", source_language: str | None = "auto") -> str:
    """Translate text using Google Cloud Translation API or Google Translate mobile web fallback."""
    if not text or not text.strip():
        return text

    source_lang = source_language or "auto"
    if target_language == source_lang or (target_language == "en" and source_lang in {"en", "", None}):
        return text

    # 1. Try official Google Cloud Translation API if key is present
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if api_key:
        try:
            body = json.dumps({
                "q": text,
                "source": None if source_lang == "auto" else source_lang,
                "target": target_language,
                "format": "text"
            }).encode("utf-8")
            request = Request(
                f"https://translation.googleapis.com/language/translate/v2?key={api_key}",
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "JanSamarth-Setu/1.0"},
                method="POST",
            )
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            translated = payload["data"]["translations"][0]["translatedText"].strip()
            if translated:
                return html.unescape(translated)
        except Exception as e:
            print(f"Google Cloud Translation API error: {e}")

    # 2. Gemini is a real, supported API (unlike the endpoints below) and a
    # key is already provisioned for this project, so prefer it over scraping.
    gemini_translated = translate_with_gemini(text, target_language=target_language, source_language=source_lang)
    if gemini_translated:
        return gemini_translated

    # 3. Use Google's lightweight endpoint before the slower mobile page.
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_language}&dt=t&q={q}"
        req = Request(url, headers={"User-Agent": "JanSamarth-Setu/1.0"})
        with urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        translated_text = "".join(item[0] for item in payload[0] if item and item[0])
        if translated_text.strip():
            return html.unescape(translated_text.strip())
    except Exception as e:
        print(f"Google Translate endpoint error: {e}")

    # 4. Mobile page fallback for environments where the lightweight endpoint
    # is unavailable.
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.google.com/m?sl={source_lang}&tl={target_language}&q={q}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as response:
            res_html = response.read().decode("utf-8")
        match = re.search(r'<div[^>]*class="result-container"[^>]*>(.*?)</div>', res_html, re.DOTALL)
        if match:
            translated = html.unescape(match.group(1).strip())
            if translated:
                return translated
    except Exception as e:
        print(f"Google Translate Mobile Endpoint error: {e}")

    return text


def translate_to_english(text: str, source_language: str | None) -> str:
    """Translate a user request to English using Google Translate service."""
    if not text or not text.strip() or source_language in {None, "", "en"}:
        return text
    return translate_text(text, target_language="en", source_language=source_language)


def translate_dict(texts: dict[str, str], target_language: str, source_language: str = "en") -> dict[str, str]:
    """Batch translate a dictionary of text items to the target language."""
    if not texts or target_language == source_language:
        return texts

    keys = list(texts)
    marker = "\n###JAN_SAMARTH_ITEM###\n"
    combined_text = marker.join(texts[key] for key in keys)
    translated = translate_text(combined_text, target_language=target_language, source_language=source_language)
    parts = translated.split(marker)
    if len(parts) == len(keys):
        return {key: parts[index].strip() for index, key in enumerate(keys)}

    # If a provider changes the marker, translate items independently rather
    # than shifting translations onto the wrong UI key.
    with ThreadPoolExecutor(max_workers=4) as executor:
        translated_values = executor.map(
            lambda key: translate_text(texts[key], target_language=target_language, source_language=source_language),
            keys,
        )
    return dict(zip(keys, translated_values))


