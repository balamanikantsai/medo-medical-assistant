"""Authentication & user management (Excel-backed, migrating to SQLite)."""

from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os

from config import get_config

cfg = get_config()
EXCEL_FILE = cfg.EXCEL_FILE


def init_user_storage():
    """Create the Excel file if it doesn't exist."""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["email", "username", "password", "language"])
        df.to_excel(EXCEL_FILE, index=False)


def add_user(email: str, username: str, password: str) -> bool:
    """Hash password and append user. Returns False if username taken."""
    init_user_storage()
    hashed = generate_password_hash(password)
    df = pd.read_excel(EXCEL_FILE)

    if username in df["username"].values:
        return False

    new_row = pd.DataFrame(
        [[email, username, hashed, "en"]],
        columns=["email", "username", "password", "language"],
    )
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    return True


def get_user(username: str):
    """Return user row as list or None."""
    init_user_storage()
    df = pd.read_excel(EXCEL_FILE)
    row = df[df["username"] == username]
    if row.empty:
        return None
    return row.iloc[0].tolist()


def get_user_language(username: str) -> str:
    """Return ISO-639 language code for the user (default 'en')."""
    try:
        df = pd.read_excel(EXCEL_FILE)
        row = df[df["username"] == username]
        return row["language"].values[0] if not row.empty else "en"
    except Exception:
        return "en"


def update_user_language(username: str, lang_code: str) -> bool:
    try:
        df = pd.read_excel(EXCEL_FILE)
        if username in df["username"].values:
            df.loc[df["username"] == username, "language"] = lang_code
            df.to_excel(EXCEL_FILE, index=False)
            return True
        return False
    except Exception:
        return False


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def check_password(password: str, stored_hash: str) -> bool:
    return check_password_hash(stored_hash, password)
