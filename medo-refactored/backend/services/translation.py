"""Google Translate wrapper."""

from config import get_config

cfg = get_config()
_client = None


def _get_client():
    global _client
    if _client is None:
        try:
            from google.cloud import translate_v2 as translate
            _client = translate.Client.from_service_account_json(
                cfg.GOOGLE_TRANSLATE_CREDENTIALS
            )
            print("✅ Google Translate client initialized")
        except Exception as e:
            print(f"⚠️ Translate init failed: {e}")
    return _client


def translate_text(texts, src_lang="en", tgt_lang="hi"):
    """Translate text(s). Returns original on failure."""
    if src_lang == tgt_lang:
        return texts

    client = _get_client()
    if client is None:
        return texts

    single = isinstance(texts, str)
    if single:
        texts = [texts]
    if not texts:
        return [] if not single else ""

    try:
        results = client.translate(texts, source_language=src_lang, target_language=tgt_lang)
        out = [r["translatedText"] if r else orig for r, orig in zip(results, texts)]
        return out[0] if single else out
    except Exception as e:
        print(f"Translation error: {e}")
        return texts[0] if single else texts
