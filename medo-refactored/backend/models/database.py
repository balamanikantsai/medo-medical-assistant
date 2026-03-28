"""SQLite database helpers — users & chat logs.

NOTE: The current implementation uses Excel (utils/auth.py) for user storage.
This module provides SQLite-based storage as an alternative.
To switch to SQLite, update the imports in routes/ to use this module.
"""

import sqlite3
from werkzeug.security import generate_password_hash
from config import get_config

cfg = get_config()


def _connect():
    return sqlite3.connect(cfg.DATABASE_PATH)


def init_db():
    """Initialize database tables. Call once at app startup if using SQLite."""
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            language TEXT DEFAULT 'en'
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            inference_time REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()
    conn.close()


def add_user(email, username, password, language="en"):
    """Add a new user. Returns True on success, False if username exists."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO users (email, username, password, language) VALUES (?, ?, ?, ?)",
            (email, username, generate_password_hash(password), language),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username):
    """Get user row by username. Returns (id, email, username, password, language) or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT id, email, username, password, language FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    return row


def get_user_language(username):
    """Get user's preferred language code."""
    conn = _connect()
    row = conn.execute(
        "SELECT language FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row[0] if row else "en"


def update_user_language(username, lang_code):
    """Update user's preferred language. Returns True on success."""
    conn = _connect()
    try:
        cursor = conn.execute(
            "UPDATE users SET language = ? WHERE username = ?",
            (lang_code, username),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()


def log_chat(username, prompt, response, inference_time):
    """Log a chat interaction."""
    conn = _connect()
    conn.execute(
        "INSERT INTO chat_logs (username, prompt, response, inference_time) VALUES (?, ?, ?, ?)",
        (username, prompt, response, inference_time),
    )
    conn.commit()
    conn.close()


def get_chat_logs(username, limit=50):
    """Get recent chat logs for a user."""
    conn = _connect()
    rows = conn.execute(
        "SELECT prompt, response, inference_time, timestamp FROM chat_logs WHERE username = ? ORDER BY timestamp DESC LIMIT ?",
        (username, limit),
    ).fetchall()
    conn.close()
    return rows
