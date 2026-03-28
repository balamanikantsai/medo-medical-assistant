"""Google Speech-to-Text & Text-to-Speech wrappers."""

import re
import os
import base64
from config import get_config

cfg = get_config()

_speech_client = None
_tts_client = None


def _get_speech_client():
    global _speech_client
    if _speech_client is None and os.path.exists(cfg.GOOGLE_SPEECH_CREDENTIALS):
        try:
            from google.cloud import speech
            _speech_client = speech.SpeechClient.from_service_account_json(
                cfg.GOOGLE_SPEECH_CREDENTIALS
            )
            print("✅ STT client initialized")
        except Exception as e:
            print(f"⚠️ STT init failed: {e}")
    return _speech_client


def _get_tts_client():
    global _tts_client
    if _tts_client is None and os.path.exists(cfg.GOOGLE_SPEECH_CREDENTIALS):
        try:
            from google.cloud import texttospeech
            _tts_client = texttospeech.TextToSpeechClient.from_service_account_json(
                cfg.GOOGLE_SPEECH_CREDENTIALS
            )
            print("✅ TTS client initialized")
        except Exception as e:
            print(f"⚠️ TTS init failed: {e}")
    return _tts_client


def transcribe_audio(audio_bytes: bytes, language_code: str = "en-US") -> str:
    """Return transcribed text or empty string."""
    client = _get_speech_client()
    if not client:
        return ""
    from google.cloud import speech

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(language_code=language_code)
    response = client.recognize(config=config, audio=audio)
    if response.results:
        return response.results[0].alternatives[0].transcript
    return ""


def synthesize_speech(text: str, language_code: str = "en-US") -> str | None:
    """Return base64-encoded MP3 or None."""
    client = _get_tts_client()
    if not client:
        return None
    from google.cloud import texttospeech

    filtered = re.sub(r"[^\w\s.,!?;:'\"()\[\]{}<>@#%&*\-+=/\\|~`$^]", "", text)
    synthesis_input = texttospeech.SynthesisInput(text=filtered)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    try:
        resp = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return base64.b64encode(resp.audio_content).decode("utf-8")
    except Exception as e:
        print(f"⚠️ TTS error: {e}")
        return None
