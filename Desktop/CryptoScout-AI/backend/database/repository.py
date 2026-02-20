

# backend/database/repository.py

import sqlite3
from datetime import datetime, timedelta
from database.db import get_connection


# =============================
# USERS
# =============================

def get_or_create_user(google_id, email, name, picture):
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
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

        return dict(user) if user else None
    except sqlite3.Error as e:
        print(f"Database error in get_or_create_user: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id):
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,)
        )

        user = cursor.fetchone()
        return dict(user) if user else None
    except sqlite3.Error as e:
        print(f"Database error in get_user_by_id: {e}")
        return None
    finally:
        if conn:
            conn.close()


# =============================
# PROJECTS
# =============================

def upsert_project(data):
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
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
            name=excluded.name,
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
    except sqlite3.Error as e:
        print(f"Database error in upsert_project: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def get_all_projects():
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()

        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        print(f"Database error in get_all_projects: {e}")
        return []
    finally:
        if conn:
            conn.close()


def insert_project_history(data):
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
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
            ai_verdict,
            sentiment_score,
            combined_score,
            snapshot_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            data["symbol"],
            data["current_price"],
            data["market_cap"],
            data["volume_24h"],
            data["price_change_24h"],
            data["price_change_7d"],
            data["ai_score"],
            data["ai_verdict"],
            data["sentiment_score"],
            data["combined_score"]
        ))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in insert_project_history: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def get_project_by_symbol(symbol: str):
    if not symbol or not isinstance(symbol, str):
        return None
    
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM projects WHERE symbol=?",
            (symbol.upper().strip(),)
        )

        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database error in get_project_by_symbol: {e}")
        return None
    finally:
        if conn:
            conn.close()


def insert_alert(symbol: str, alert_type: str, message: str):
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO alerts (symbol, alert_type, message, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """, (symbol.upper().strip(), alert_type, message))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in insert_alert: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def get_recent_alert(symbol: str, alert_type: str, minutes: int = 60):
    """
    Prevent duplicate alerts within time window.
    """
    if not symbol or not alert_type:
        return None

    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM alerts
        WHERE symbol=? AND alert_type=? 
        AND created_at >= datetime('now', ?)
        ORDER BY created_at DESC
        LIMIT 1
        """, (symbol.upper().strip(), alert_type, f"-{minutes} minutes"))

        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database error in get_recent_alert: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_all_alerts(limit: int = 50):
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM alerts
        ORDER BY created_at DESC
        LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        print(f"Database error in get_all_alerts: {e}")
        return []
    finally:
        if conn:
            conn.close()


# =====================================================
# REFRESH TOKENS
# =====================================================

def store_refresh_token(user_id: int, token: str, days_valid: int = 30):
    """
    Store refresh token in DB.
    Allows revocation and multi-session tracking.
    """
    if not user_id or not token:
        return False

    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        expires_at = (datetime.utcnow() + timedelta(days=days_valid)).isoformat()

        cursor.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, expires_at)
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                token,
                expires_at
            )
        )

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in store_refresh_token: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def is_refresh_token_valid(token: str) -> bool:
    """
    Check whether refresh token exists and is valid.
    """
    if not token:
        return False

    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM refresh_tokens
            WHERE token = ? AND expires_at > ?
            """,
            (token, datetime.utcnow().isoformat())
        )

        row = cursor.fetchone()
        return row is not None
    except sqlite3.Error as e:
        print(f"Database error in is_refresh_token_valid: {e}")
        return False
    finally:
        if conn:
            conn.close()


def revoke_refresh_token(token: str):
    """
    Delete a refresh token (logout support).
    """
    if not token:
        return False

    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM refresh_tokens
            WHERE token = ?
            """,
            (token,)
        )

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in revoke_refresh_token: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()