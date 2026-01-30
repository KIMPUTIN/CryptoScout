
import sqlite3
import os


# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "cryptoscout.db")


# --------------------------------------------------
# Initialize Database
# --------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        symbol TEXT,

        score REAL,
        verdict TEXT,
        confidence REAL,
        reasons TEXT
    )
    """)

    # Auto-migrate: add confidence column if missing
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN confidence REAL")
        print("✅ Added confidence column")
    except:
        pass

    conn.commit()
    conn.close()


# --------------------------------------------------
# Fetch All Projects
# --------------------------------------------------
def get_all_projects():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            name,
            symbol,
            score,
            verdict,
            confidence,
            reasons
        FROM projects
        ORDER BY score DESC
    """)

    rows = cursor.fetchall()

    projects = []

    for row in rows:
        projects.append({
            "name": row["name"],
            "symbol": row["symbol"],
            "score": row["score"],
            "verdict": row["verdict"],
            "confidence": row["confidence"],
            "reasons": row["reasons"],
        })

    conn.close()
    return projects


# --------------------------------------------------
# Seed Test Data (First Run Only)
# --------------------------------------------------
def seed_test_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]

    if count == 0:
        print("📦 Seeding test data (first run)...")

        cursor.execute("""
            INSERT INTO projects
            (name, symbol, score, verdict, confidence, reasons)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "NovaChain",
            "NOVA",
            88,
            "Strong Buy",
            0.92,
            "High social growth, strong dev activity, low market cap"
        ))

        cursor.execute("""
            INSERT INTO projects
            (name, symbol, score, verdict, confidence, reasons)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "MetaPulse",
            "MPX",
            72,
            "Buy",
            0.78,
            "Good tokenomics, early exchange listing, rising volume"
        ))

        conn.commit()
        print("✅ Test data seeded")

    else:
        print(f"📊 Database already has {count} projects, skipping seed")

    conn.close()


# --------------------------------------------------
# Save / Update Project
# --------------------------------------------------
def save_project(project):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Safety defaults
        score = float(project.get("score", 0))
        confidence = float(project.get("confidence", 0.5))
        reasons = project.get("reasons", "")

        # Auto verdict
        if score >= 75:
            verdict = "Strong Buy"
        elif score >= 55:
            verdict = "Buy"
        elif score >= 40:
            verdict = "Hold"
        else:
            verdict = "Avoid"

        project["verdict"] = verdict

        # Check if exists
        cursor.execute("""
            SELECT id FROM projects
            WHERE name = ? AND symbol = ?
        """, (project["name"], project["symbol"]))

        existing = cursor.fetchone()

        # -----------------------
        # UPDATE
        # -----------------------
        if existing:

            cursor.execute("""
                UPDATE projects
                SET
                    score = ?,
                    verdict = ?,
                    confidence = ?,
                    reasons = ?
                WHERE id = ?
            """, (
                score,
                verdict,
                confidence,
                reasons,
                existing[0]
            ))

        # -----------------------
        # INSERT
        # -----------------------
        else:

            cursor.execute("""
                INSERT INTO projects
                (name, symbol, score, verdict, confidence, reasons)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project["name"],
                project["symbol"],
                score,
                verdict,
                confidence,
                reasons
            ))

        conn.commit()

    except Exception as e:
        print(f"⚠️ Error saving project {project.get('name', 'unknown')}: {e}")
        conn.rollback()

    finally:
        conn.close()

