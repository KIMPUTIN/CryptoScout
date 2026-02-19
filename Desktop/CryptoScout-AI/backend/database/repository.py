
# backend/database/repository.py

from datetime import datetime
from database.db import get_connection


# =============================
# USERS
# =============================

def get_or_create_user(google_id, email, name, picture):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE google_id=?",
        (google_id,)
    )
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (google_id, email, name, picture) VALUES (?, ?, ?, ?)",
            (google_id, email, name, picture)
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM users WHERE google_id=?",
            (google_id,)
        )
        user = cursor.fetchone()

    conn.close()
    return dict(user)


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


# =============================
# PROJECTS
# =============================

def upsert_project(data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO projects (
        name, symbol, current_price, market_cap, volume_24h,
        price_change_24h, price_change_7d,
        market_cap_rank, ai_score, ai_verdict,
        sentiment_score, last_updated
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(symbol) DO UPDATE SET
        market_cap=excluded.market_cap,
        current_price=excluded.current_price,
        volume_24h=excluded.volume_24h,
        price_change_24h=excluded.price_change_24h,
        price_change_7d=excluded.price_change_7d,
        market_cap_rank=excluded.market_cap_rank,
        ai_score=excluded.ai_score,
        ai_verdict=excluded.ai_verdict,
        sentiment_score=excluded.sentiment_score,
        last_updated=excluded.last_updated
    """, (
        data["name"],
        data["symbol"],
        data["current_price"],
        data["market_cap"],
        data["volume_24h"],
        data["price_change_24h"],
        data["price_change_7d"],
        data["market_cap_rank"],
        data["ai_score"],
        data["ai_verdict"],
        data["sentiment_score"],
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_all_projects():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM projects")
    rows = cursor.fetchall()

    conn.close()
    return [dict(r) for r in rows]


def insert_project_history(data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO project_history (
        symbol,
        current_price,
        market_cap,
        volume_24h,
        price_change_24h,
        price_change_7d,
        ai_score,
        sentiment_score,
        combined_score,
        snapshot_time
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        data["symbol"],
        data["current_price"],
        data["market_cap"],
        data["volume_24h"],
        data["price_change_24h"],
        data["price_change_7d"],
        data["ai_score"],
        data["sentiment_score"],
        data["combined_score"]
    ))

    conn.commit()
    conn.close()


def get_project_by_symbol(symbol: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM projects WHERE symbol=?",
        (symbol.upper(),)
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def insert_alert(symbol: str, alert_type: str, message: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO alerts (symbol, alert_type, message, created_at)
    VALUES (?, ?, ?, datetime('now'))
    """, (symbol.upper(), alert_type, message))

    conn.commit()
    conn.close()


def get_recent_alert(symbol: str, alert_type: str, minutes: int = 60):
    """
    Prevent duplicate alerts within time window.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM alerts
    WHERE symbol=? AND alert_type=? 
    AND created_at >= datetime('now', ?)
    ORDER BY created_at DESC
    LIMIT 1
    """, (symbol.upper(), alert_type, f"-{minutes} minutes"))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_all_alerts(limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM alerts
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]
