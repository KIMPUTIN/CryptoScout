
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "cryptoscout.db")


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
    """Only seed test data if database is empty (first run only)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if database already has projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]

    # Only seed if database is empty
    if count == 0:
        print("📦 Seeding test data (first run)...")
        cursor.execute(
            """
            INSERT INTO projects (name, symbol, score, verdict, reasons)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "NovaChain",
                "NOVA",
                88,
                "Strong Buy",
                "High social growth, strong dev activity, low market cap",
            ),
        )

        cursor.execute(
            """
            INSERT INTO projects (name, symbol, score, verdict, reasons)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "MetaPulse",
                "MPX",
                72,
                "Buy",
                "Good tokenomics, early exchange listing, rising volume",
            ),
        )

        conn.commit()
        print("✅ Test data seeded")
    else:
        print(f"📊 Database already has {count} projects, skipping seed")

    conn.close()


def save_project(project):
    """Save or update a project. Updates if name+symbol already exists."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Auto-generate verdict if missing
        score = project.get("score", 0)

        if score >= 75:
            verdict = "Strong Buy"
        elif score >= 55:
            verdict = "Buy"
        elif score >= 40:
            verdict = "Hold"
        else:
            verdict = "Avoid"

        project["verdict"] = verdict

        # Check if project already exists
        cursor.execute("""
            SELECT id FROM projects 
            WHERE name = ? AND symbol = ?
        """, (project["name"], project["symbol"]))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing project
            cursor.execute("""
                UPDATE projects 
                SET score = ?, verdict = ?, reasons = ?
                WHERE id = ?
            """, (
                project["score"],
                project["verdict"],
                project["reasons"],
                existing[0]
            ))
        else:
            # Insert new project
            cursor.execute("""
                INSERT INTO projects (name, symbol, score, verdict, reasons)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project["name"],
                project["symbol"],
                project["score"],
                project["verdict"],
                project["reasons"]
            ))
        
        conn.commit()

    except Exception as e:
        print(f"⚠️ Error saving project {project.get('name', 'unknown')}: {e}")
        conn.rollback()

    finally:
        conn.close()

