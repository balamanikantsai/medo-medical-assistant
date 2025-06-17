from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os

EXCEL_FILE = "users.xlsx"

def init_user_storage():
    """Initialize the user storage file if it doesn't exist."""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["email", "username", "password"])
        df.to_excel(EXCEL_FILE, index=False)

def add_user(email, username, password):
    """Stores user details in an Excel file."""
    hashed_password = generate_password_hash(password)
    df = pd.read_excel(EXCEL_FILE)
    
    if username in df["username"].values:
        return False  # User already exists
    
    new_user = pd.DataFrame([[email, username, hashed_password,"en"]], columns=["email", "username", "password","language"])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    return True

def get_user(username):
    """Retrieves user details from the Excel file."""
    df = pd.read_excel(EXCEL_FILE)
    
    user_data = df[df["username"] == username]
    
    if user_data.empty:
        return None
    
    return user_data.iloc[0].tolist()  # Returns user row as a list

def hash_password(password):
    """Hashes a password using Werkzeug."""
    return generate_password_hash(password)

def check_password(password, stored_hash):
    """Checks if a password matches the stored hash."""
    return check_password_hash(stored_hash, password)
