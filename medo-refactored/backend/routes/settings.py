"""Settings routes — language preferences."""

from flask import Blueprint, request, jsonify, session
from config import get_config
from utils.auth import get_user_language, update_user_language

cfg = get_config()
settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@settings_bp.route("", methods=["GET"])
def get_settings():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Unauthorized"}), 403

    current = get_user_language(username)
    return jsonify({
        "current_language": current,
        "supported_languages": cfg.SUPPORTED_LANGUAGES,
    })


@settings_bp.route("/language", methods=["PUT"])
def change_language():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    lang = data.get("language", "").strip()

    if lang not in cfg.SUPPORTED_LANGUAGES:
        return jsonify({"error": f"Unsupported language: {lang}"}), 400

    ok = update_user_language(username, lang)
    if ok:
        return jsonify({"message": "Language updated.", "language": lang})
    return jsonify({"error": "Failed to update language."}), 500
