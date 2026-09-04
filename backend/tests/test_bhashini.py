import services.bhashini as bhashini
from services.bhashini import translate_to_english


def test_local_fallback_when_no_provider_is_configured(monkeypatch):
    monkeypatch.delenv("BHASHINI_GATEWAY_URL", raising=False)
    monkeypatch.delenv("BHASHINI_API_KEY", raising=False)
    monkeypatch.setattr(bhashini, "translate_with_gemini", lambda *a, **k: None)
    translated, provider = translate_to_english("मुझे ऋण चाहिए", "hi")
    assert translated == "मुझे ऋण चाहिए"
    assert provider == "local"


def test_gemini_fallback_when_bhashini_is_not_configured(monkeypatch):
    monkeypatch.delenv("BHASHINI_GATEWAY_URL", raising=False)
    monkeypatch.delenv("BHASHINI_API_KEY", raising=False)
    monkeypatch.setattr(bhashini, "translate_with_gemini", lambda *a, **k: "I need a loan")
    translated, provider = translate_to_english("मुझे ऋण चाहिए", "hi")
    assert translated == "I need a loan"
    assert provider == "gemini"


def test_english_source_skips_translation_entirely(monkeypatch):
    calls = []
    monkeypatch.setattr(bhashini, "translate_with_gemini", lambda *a, **k: calls.append(1))
    translated, provider = translate_to_english("I need a loan", "en")
    assert translated == "I need a loan"
    assert provider == "local"
    assert calls == []
