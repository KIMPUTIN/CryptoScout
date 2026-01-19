
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "cryptoscout.db")

DB_NAME = "cryptoscout.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        symbol TEXT,
        score INTEGER,
        verdict TEXT,
        reasons TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_all_projects():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM projects ORDER BY score DESC")
    rows = cursor.fetchall()

    projects = []
    for row in rows:
        projects.append({
            "id": row["id"],
            "name": row["name"],
            "symbol": row["symbol"],
            "score": row["score"],
            "verdict": row["verdict"],
            "reasons": row["reasons"],
        })

    conn.close()
    return projects

    def seed_test_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM projects")

    cursor.execute("""
        INSERT INTO projects (name, symbol, score, verdict, reasons)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "NovaChain",
        "NOVA",
        88,
        "Strong Buy",
        "High social growth, strong dev activity, low market cap"
    ))

    cursor.execute("""
        INSERT INTO projects (name, symbol, score, verdict, reasons)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "MetaPulse",
        "MPX",
        72,
        "Buy",
        "Good tokenomics, early exchange listing, rising volume"
    ))

    conn.commit()
    conn.close()

print("DB FILE PATH:", DB_NAME)
