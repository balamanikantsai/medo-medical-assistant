"""OpenRouter API wrapper — interact with Nemotron Super and other models."""

import json
import requests
from config import get_config

cfg = get_config()


def call_openrouter_api(user_message: str, system_prompt: str = None, temperature: float = None) -> str:
    """
    Call OpenRouter API with the specified model.

    Args:
        user_message: The user's query/prompt
        system_prompt: Optional system prompt for context
        temperature: Optional temperature override

    Returns:
        The model's response text
    """
    headers = {
        "Authorization": f"Bearer {cfg.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-OpenRouter-Title": "Medo Medical Assistant",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": cfg.OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": cfg.OPENROUTER_MAX_TOKENS,
        "temperature": temperature if temperature is not None else cfg.OPENROUTER_TEMPERATURE,
    }

    try:
        response = requests.post(
            cfg.OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=90
        )
        response.raise_for_status()
        result = response.json()

        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        return "I apologize, but I couldn't generate a response. Please try again."

    except requests.exceptions.Timeout:
        print("OpenRouter API error: Request timed out")
        return "The request took too long. Please try a simpler question or try again later."
    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API error: {e}")
        return "Error connecting to the AI service. Please try again later."


def generate_medical_answer(user_query: str, search_context: str = "") -> str:
    """
    Generate a medical answer using OpenRouter's Nemotron model.
    """
    system_prompt = (
        "You are Medo, an expert medical assistant. Provide clear, concise, "
        "empathetic, and safe responses using simple language. "
        "Think through complex medical questions carefully before answering."
    )

    user_content = f'User Query: "{user_query}"'
    if search_context:
        user_content += f'\n\nRelevant Information:\n---\n{search_context}\n---'
    else:
        user_content += "\n\nAnswer based on your medical knowledge."

    user_content += (
        "\n\nIMPORTANT:\n"
        "- If the query is NOT medical, politely state you only handle medical questions.\n"
        "- Prioritize safety. Advise seeking professional medical help for serious concerns.\n"
        "- Keep the response concise and use clear paragraphs.\n"
        "- Include relevant emojis if appropriate."
    )

    return call_openrouter_api(user_content, system_prompt=system_prompt, temperature=cfg.LLM_ANSWER_TEMPERATURE)
