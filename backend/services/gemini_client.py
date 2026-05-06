import os
import sys
from functools import lru_cache
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

_LAST_ERROR = {"type": None, "message": None}


@lru_cache(maxsize=1)
def _model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return genai.GenerativeModel(model_name)


def model_name():
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def has_key():
    return bool(os.getenv("GEMINI_API_KEY"))


def last_error():
    return dict(_LAST_ERROR)


def generate_text(prompt):
    model = _model()
    if model is None:
        return "Gemini API key is not configured."

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        _LAST_ERROR["type"] = type(e).__name__
        _LAST_ERROR["message"] = str(e)[:280]
        print(f"Gemini API error: {type(e).__name__}: {e}", file=sys.stderr)
        return "I'm having trouble thinking right now. Please try again."

    if not response or not getattr(response, "text", None):
        _LAST_ERROR["type"] = "EmptyResponse"
        _LAST_ERROR["message"] = "Model returned no text (often a safety filter)."
        return "I couldn't think of a good response. Please try again."

    # Successful call — clear last error
    _LAST_ERROR["type"] = None
    _LAST_ERROR["message"] = None
    return response.text.strip()


def probe():
    """Lightweight 'are you there?' call. Returns a structured dict suitable
    for a status endpoint. Caches a successful probe for 5 minutes so we
    don't hammer Gemini on every dashboard load."""
    import time

    if not has_key():
        return {
            "configured": False,
            "ok": False,
            "model": model_name(),
            "reason": "GEMINI_API_KEY is not set in the backend environment.",
            "last_error": last_error(),
        }

    now = time.time()
    cache = probe._cache  # type: ignore[attr-defined]
    if cache and (now - cache["ts"] < 300):
        return cache["result"]

    text = generate_text("Reply with the single word: pong")
    text_lower = (text or "").lower()
    is_error_string = (
        "api key" in text_lower
        or "trouble thinking" in text_lower
        or "couldn't think" in text_lower
    )
    ok = bool(text) and not is_error_string

    result = {
        "configured": True,
        "ok": ok,
        "model": model_name(),
        "sample_response": text[:120] if text else None,
        "reason": None if ok else "Gemini call did not return a usable response.",
        "last_error": last_error(),
    }
    cache = {"ts": now, "result": result}
    probe._cache = cache  # type: ignore[attr-defined]
    return result


probe._cache = None  # type: ignore[attr-defined]
