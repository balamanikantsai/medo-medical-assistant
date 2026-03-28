"""NVIDIA API wrapper — interact with kimi-k2.5 or other NVIDIA hosted models."""

import json
import requests
from config import get_config

cfg = get_config()


def call_nvidia_api(user_message: str, system_prompt: str = None, thinking: bool = True) -> str:
    """
    Call NVIDIA API with the specified model.

    Args:
        user_message: The user's query/prompt
        system_prompt: Optional system prompt for context
        thinking: Whether to enable extended thinking (for Kimi model)

    Returns:
        The model's response text
    """
    headers = {
        "Authorization": f"Bearer {cfg.NVIDIA_API_KEY}",
        "Accept": "text/event-stream" if cfg.NVIDIA_STREAM else "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": cfg.NVIDIA_MODEL,
        "messages": messages,
        "max_tokens": cfg.NVIDIA_MAX_TOKENS,
        "temperature": cfg.NVIDIA_TEMPERATURE,
        "top_p": cfg.NVIDIA_TOP_P,
        "stream": cfg.NVIDIA_STREAM,
        "chat_template_kwargs": {"thinking": thinking},
    }

    try:
        # Extended timeout for complex queries with thinking enabled
        timeout = 120 if thinking else 60
        response = requests.post(cfg.NVIDIA_API_URL, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()

        if cfg.NVIDIA_STREAM:
            # Collect streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    # Parse SSE format: data: {...}
                    if decoded_line.startswith("data:"):
                        data_content = decoded_line[5:].strip()
                        # Handle end of stream marker
                        if data_content == "[DONE]":
                            break
                        try:
                            data = json.loads(data_content)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    full_response += delta["content"]
                        except json.JSONDecodeError:
                            # Skip malformed JSON chunks
                            continue
            return full_response if full_response else "I apologize, but I couldn't generate a response. Please try again."
        else:
            # Non-streaming response
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            return "I apologize, but I couldn't generate a response. Please try again."

    except requests.exceptions.Timeout:
        print("NVIDIA API error: Request timed out")
        return "The request took too long. Please try a simpler question or try again later."
    except requests.exceptions.RequestException as e:
        print(f"NVIDIA API error: {e}")
        return f"Error connecting to the AI service. Please try again later."


def generate_medical_answer(user_query: str, search_context: str = "") -> str:
    """
    Generate a medical answer using NVIDIA's Kimi model with extended thinking.
    """
    system_prompt = (
        "You are Medo, an expert medical assistant. Provide clear, concise, "
        "empathetic, and safe responses using simple language. "
        "Use extended thinking to reason through complex medical questions carefully."
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
        "- Include relevant emojis if appropriate. 😊"
    )
    
    return call_nvidia_api(user_content, system_prompt=system_prompt, thinking=True)
