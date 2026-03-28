"""Firecrawl web-search wrapper."""

import requests
from config import get_config

cfg = get_config()


def firecrawl_search(query: str, limit: int | None = None):
    """Return (context_string, sources_list)."""
    url = "https://api.firecrawl.dev/v1/search"
    payload = {
        "limit": limit or cfg.FIRECRAWL_SEARCH_LIMIT,
        "query": query,
        "extractorOptions": {
            "mode": "llm-extraction",
            "extractionSchema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "source": {"type": "string"},
                },
            },
        },
    }
    headers = {
        "Authorization": f"Bearer {cfg.FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        results = resp.json().get("data", [])
        sources = []
        for r in results:
            ext = r.get("llm_extraction", {})
            if ext:
                sources.append({"text": ext.get("summary", ""), "url": ext.get("source", "")})
        sources = sources[:4]
        context = "\n".join(s["text"] for s in sources if s["text"])
        return context, sources
    except Exception as e:
        print(f"Search error: {e}")
        return "", []
