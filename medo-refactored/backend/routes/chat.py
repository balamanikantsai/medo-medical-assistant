"""Chat routes — main Q&A endpoint + audio transcription."""

import time
from flask import Blueprint, request, jsonify, session
from config import get_config
from utils.auth import get_user_language
from services.translation import translate_text
from services.speech import transcribe_audio, synthesize_speech
from services.search import firecrawl_search
from services.llm import decide_search
from services.openrouter import generate_medical_answer

cfg = get_config()
chat_bp = Blueprint("chat", __name__, url_prefix="/api")


@chat_bp.route("/chat", methods=["POST"])
def get_response():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Unauthorized"}), 403

    start_time = time.time()
    user_lang = get_user_language(username)
    data = request.get_json(silent=True) or {}
    user_prompt = data.get("prompt", "").strip()

    if not user_prompt:
        return jsonify({"error": "Empty prompt received"}), 400

    # Translate to English if needed
    processing_prompt = user_prompt
    if user_lang != "en":
        translated = translate_text(user_prompt, src_lang=user_lang, tgt_lang="en")
        if isinstance(translated, str):
            processing_prompt = translated
        elif isinstance(translated, list) and translated:
            processing_prompt = translated[0]

    # Decide whether web search is needed
    needs_search, search_query = decide_search(processing_prompt)
    search_context = ""
    sources = []

    if needs_search and search_query:
        search_context, sources = firecrawl_search(search_query)
        if not search_context:
            search_context = "No specific context found from web search."

    # Generate answer using OpenRouter API
    english_answer = generate_medical_answer(processing_prompt, search_context)

    # Translate back if needed
    final_answer = english_answer
    if user_lang != "en":
        translated = translate_text(english_answer, src_lang="en", tgt_lang=user_lang)
        if isinstance(translated, str):
            final_answer = translated
        elif isinstance(translated, list) and translated:
            final_answer = translated[0]

    # Synthesize speech
    audio_content_base64 = None
    tts_lang = cfg.BCP47_MAP.get(user_lang, "en-US")
    audio_content_base64 = synthesize_speech(final_answer, language_code=tts_lang)

    inference_time = round(time.time() - start_time, 2)

    return jsonify({
        "response": final_answer,
        "inference_time": inference_time,
        "sources": sources,
        "audio_content": audio_content_base64,
    })


@chat_bp.route("/transcribe", methods=["POST"])
def transcribe():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Unauthorized"}), 403

    if "audio_blob" not in request.files:
        return jsonify({"error": "No audio data received."}), 400

    audio_file = request.files["audio_blob"]
    user_lang = get_user_language(username)
    bcp47 = cfg.BCP47_MAP.get(user_lang, "en-US")

    try:
        content = audio_file.read()
        transcript = transcribe_audio(content, language_code=bcp47)
        return jsonify({"transcript": transcript})
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {e}"}), 500
