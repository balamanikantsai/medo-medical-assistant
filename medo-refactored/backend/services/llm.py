"""LLM wrapper — search decisions, answer generation, prescription parsing via OpenRouter."""

import json
import requests
from config import get_config

cfg = get_config()


def _call_openrouter(messages: list, max_tokens: int = 256, temperature: float = 0.7) -> str | None:
    """Internal helper to call OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {cfg.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-OpenRouter-Title": "Medo Medical Assistant",
    }

    payload = {
        "model": cfg.OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        response = requests.post(cfg.OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"].strip()
        return None
    except requests.exceptions.Timeout:
        print("OpenRouter API error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API error: {e}")
        return None


def decide_search(prompt: str) -> tuple[bool, str]:
    """
    Use OpenRouter API to decide if search is needed.
    Return (needs_search, search_query_or_empty).
    """
    decision_prompt = (
        'You are Medo, a helpful medical assistant. Analyze the following user query:\n'
        f'"{prompt}"\n\n'
        'Is external web search REQUIRED to provide an accurate, up-to-date, and safe medical answer?\n'
        '- If YES, respond ONLY with: [SEARCH_NEEDED] followed by the best search query.\n'
        '- If NO (e.g., greeting, simple definition, non-medical), respond ONLY with: [NO_SEARCH_NEEDED].'
    )

    messages = [{"role": "user", "content": decision_prompt}]
    text = _call_openrouter(messages, max_tokens=256, temperature=cfg.LLM_DECISION_TEMPERATURE)

    if text:
        if text.startswith("[SEARCH_NEEDED]"):
            query = text.replace("[SEARCH_NEEDED]", "").strip()
            return (True, query) if query else (False, "")
    return False, ""


def generate_answer(user_query: str, search_context: str = "") -> str:
    """Generate medical answer using OpenRouter."""
    from services.openrouter import generate_medical_answer
    return generate_medical_answer(user_query, search_context)


def parse_prescription(prescription_text: str) -> dict | None:
    """Parse prescription text into structured JSON via OpenRouter LLM. Returns dict or None."""
    prompt = (
        "You are an expert medical prescription parser. Analyze the following "
        "prescription text and extract the diagnosis (if present) and medication details.\n"
        "Return the information ONLY as a valid JSON object with the following structure:\n"
        "{\n"
        '  "diagnosis": "...",\n'
        '  "medications": [\n'
        "    {\n"
        '      "name": "...",\n'
        '      "dosage": "...",\n'
        '      "frequency": "...",\n'
        '      "timing": "..." // Extract specific times, keywords, and instructions.\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "If information is missing for a field, use null or an empty string.\n\n"
        f"Prescription Text:\n---\n{prescription_text}\n---\n\nJSON Output:"
    )

    messages = [{"role": "user", "content": prompt}]
    content = _call_openrouter(messages, max_tokens=1024, temperature=cfg.LLM_PARSE_TEMPERATURE)

    if not content:
        print("Prescription parse error: Empty response from LLM")
        return None

    try:
        # Strip markdown fences
        if content.startswith("```json"):
            content = content[len("```json"):].strip()
        elif content.startswith("```"):
            content = content[len("```"):].strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        data = json.loads(content)
        if not isinstance(data, dict):
            return None
        if "medications" not in data:
            data["medications"] = []
        elif not isinstance(data.get("medications"), list):
            return None
        return data
    except json.JSONDecodeError as e:
        print(f"Prescription parse error (JSON): {e}")
        return None
    except Exception as e:
        print(f"Prescription parse error: {e}")
        return None
