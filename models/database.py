import sqlite3
from config import DATABASE_PATH
from utils.auth import hash_password

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    
    # Create chat logs table
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        inference_time REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def add_user(email, username, password):
    """Add a new user to the database with a salted hash."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)  # Store the salted hash
    
    try:
        cursor.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)", 
                       (email, username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username or email already exists
    finally:
        conn.close()



def log_chat(username, prompt, response, inference_time):
    """Log the user's chat interaction with the model."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_logs (username, prompt, response, inference_time) VALUES (?, ?, ?, ?)", 
                   (username, prompt, response, inference_time))
    conn.commit()
    conn.close()

def get_chat_logs(username):
    """Retrieve chat history for a specific user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt, response, inference_time, timestamp FROM chat_logs WHERE username = ? ORDER BY timestamp DESC", 
                   (username,))
    logs = cursor.fetchall()
    conn.close()
    return logs
