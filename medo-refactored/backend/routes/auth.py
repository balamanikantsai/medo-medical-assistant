"""Authentication routes — login, register, logout (JSON API)."""

from flask import Blueprint, request, jsonify, session
from utils.auth import add_user, get_user, check_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    user = get_user(username)
    if user and len(user) > 2:
        stored_hash = user[2]  # (email, username, password, language)
        if check_password(password, stored_hash):
            session["user"] = username
            return jsonify({"message": "Login successful", "username": username}), 200

    return jsonify({"error": "Invalid username or password."}), 401


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not email or not username or not password:
        return jsonify({"error": "All fields are required."}), 400

    # Password policy
    if (
        len(password) < 8
        or not any(c.isupper() for c in password)
        or not any(c.isdigit() for c in password)
    ):
        return jsonify({
            "error": "Password must be at least 8 characters with an uppercase letter and a digit."
        }), 400

    success = add_user(email, username, password)
    if not success:
        return jsonify({"error": "Username already exists."}), 409

    return jsonify({"message": "Registration successful. Please log in."}), 201


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out."}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return current session user (for React to check auth state)."""
    username = session.get("user")
    if not username:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "username": username}), 200
