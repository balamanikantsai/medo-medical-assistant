"""Medo Medical Assistant — Flask Application Factory."""

import os
from flask import Flask
from flask_cors import CORS
from config import get_config

cfg = get_config()


def create_app():
    app = Flask(__name__)
    app.secret_key = cfg.SECRET_KEY

    # Session cookie security settings
    app.config.update(
        SESSION_COOKIE_SECURE=not cfg.DEBUG,  # HTTPS only in production
        SESSION_COOKIE_HTTPONLY=True,         # Prevent JavaScript access
        SESSION_COOKIE_SAMESITE='Lax',        # CSRF protection
    )

    # CORS — allow the React dev-server origin
    CORS(
        app,
        supports_credentials=True,
        origins=[cfg.FRONTEND_ORIGIN],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Ensure upload directory exists
    os.makedirs(cfg.UPLOAD_FOLDER, exist_ok=True)

    # Initialize user storage (Excel file)
    from utils.auth import init_user_storage
    init_user_storage()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.chat import chat_bp
    from routes.settings import settings_bp
    from routes.prescription import prescription_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(prescription_bp)

    # Health-check
    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=cfg.DEBUG, port=5000)
