
# backend/database/db.py

import sqlite3
from core.config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    CREATE INDEX IF NOT EXISTS idx_symbol_time
    ON project_history(symbol, snapshot_time);



    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_id TEXT UNIQUE,
        email TEXT,
        name TEXT,
        picture TEXT
    )
    """)

    # Projects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        symbol TEXT UNIQUE,
        current_price REAL,
        market_cap REAL,
        volume_24h REAL,
        price_change_24h REAL,
        price_change_7d REAL,
        market_cap_rank INTEGER,
        ai_score REAL,
        ai_verdict TEXT,
        sentiment_score REAL,
        last_updated TEXT
    )
    """)

    # Watchlist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        symbol TEXT,
        UNIQUE(user_id, symbol)
    )
    """)

    conn.commit()
    conn.close()

    # Historical Snapshots
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        current_price REAL,
        market_cap REAL,
        volume_24h REAL,
        price_change_24h REAL,
        price_change_7d REAL,
        ai_score REAL,
        sentiment_score REAL,
        combined_score REAL,
        snapshot_time TEXT
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        current_price REAL,
        market_cap REAL,
        volume_24h REAL,
        price_change_24h REAL,
        price_change_7d REAL,
        ai_score REAL,
        sentiment_score REAL,
        combined_score REAL,
        snapshot_time TEXT
    )
    """)



    # Alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        alert_type TEXT,
        message TEXT,
        created_at TEXT,
        is_read INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_alert_symbol_time
    ON alerts(symbol, created_at)
    """)


    # Projects indexes
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_symbol
    ON projects(symbol)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_ai_score
    ON projects(ai_score)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_projects_market_cap
    ON projects(market_cap)
    """)

    # History indexes
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_history_symbol_time
    ON project_history(symbol, snapshot_time)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT,
        expires_at TEXT
)
""")



