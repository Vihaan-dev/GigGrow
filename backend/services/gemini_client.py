import os
from functools import lru_cache
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


@lru_cache(maxsize=1)
def _model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name)


def generate_text(prompt):
    model = _model()
    if model is None:
        return "Gemini API key is not configured."

    try:
        response = model.generate_content(prompt)
    except Exception:
        return "Gemini request failed."

    if not response or not getattr(response, "text", None):
        return "Gemini did not return a response."

    return response.text.strip()
