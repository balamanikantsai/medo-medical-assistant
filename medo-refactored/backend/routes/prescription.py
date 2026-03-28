"""Prescription upload & calendar-event creation routes."""

import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from config import get_config
from services.llm import parse_prescription
from services.calendar import create_calendar_event

cfg = get_config()
prescription_bp = Blueprint("prescription", __name__, url_prefix="/api/prescription")


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in cfg.ALLOWED_EXTENSIONS


@prescription_bp.route("/upload", methods=["POST"])
def upload():
    username = session.get("user")
    if not username:
        return jsonify({"error": "Unauthorized"}), 403

    if "prescriptionFile" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["prescriptionFile"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not _allowed(file.filename):
        return jsonify({"error": "File type not allowed. Please upload a .txt file."}), 400

    filename = secure_filename(file.filename)
    upload_dir = cfg.UPLOAD_FOLDER
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    try:
        file.save(filepath)

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        if not text.strip():
            _cleanup(filepath)
            return jsonify({"error": "File content is empty."}), 400

        parsed = parse_prescription(text)
        if not parsed:
            _cleanup(filepath)
            return jsonify({"error": "Failed to parse prescription via LLM."}), 500

        success, message = create_calendar_event(parsed)
        _cleanup(filepath)

        if success:
            return jsonify({"message": message, "parsed_data": parsed}), 200
        return jsonify({"error": message, "parsed_data": parsed}), 500

    except Exception as e:
        _cleanup(filepath)
        return jsonify({"error": f"Unexpected error: {e}"}), 500


def _cleanup(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
