import sqlite3
import bcrypt

DB_FILE = "users.db"

def init_db():
    """Initializes the persistent user database table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'Free',
            manager_id INTEGER DEFAULT 3582518,
            league_id INTEGER DEFAULT 888101,
            bank_balance REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(username, password) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        hashed = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash, tier, manager_id, league_id, bank_balance FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password(password, user[1]):
        return {
            "username": user[0],
            "tier": user[2],
            "manager_id": user[3],
            "league_id": user[4],
            "bank_balance": user[5]
        }
    return None

def update_user_profile(username, manager_id, league_id, bank_balance):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET manager_id = ?, league_id = ?, bank_balance = ? 
        WHERE username = ?
    ''', (manager_id, league_id, bank_balance, username))
    conn.commit()
    conn.close()

def update_user_tier(username, tier):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tier = ? WHERE username = ?", (tier, username))
    conn.commit()
    conn.close()
