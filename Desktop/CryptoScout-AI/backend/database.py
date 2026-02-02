
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

    # Main table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,
        symbol TEXT,

        market_cap REAL,
        volume_24h REAL,
        price_change_24h REAL,
        price_change_7d REAL,

        score REAL,
        verdict TEXT,
        confidence REAL,
        reasons TEXT
    )
    """)

    # Auto-migrate missing columns (safe in production)
    columns = {
        "market_cap": "REAL",
        "volume_24h": "REAL",
        "price_change_24h": "REAL",
        "price_change_7d": "REAL",
        "confidence": "REAL"
    }

    cursor.execute("PRAGMA table_info(projects)")
    existing = [row[1] for row in cursor.fetchall()]

    for col, col_type in columns.items():
        if col not in existing:
            cursor.execute(
                f"ALTER TABLE projects ADD COLUMN {col} {col_type}"
            )
            print(f"✅ Added column: {col}")

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

            market_cap,
            volume_24h,
            price_change_24h,
            price_change_7d,

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
        projects.append(dict(row))

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
    """Insert or update project safely"""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        score = project.get("score", 0)

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

        data = (
            project.get("market_cap", 0),
            project.get("volume_24h", 0),
            project.get("price_change_24h", 0),
            project.get("price_change_7d", 0),

            project.get("score", 0),
            project.get("verdict", ""),
            project.get("confidence", 0),
            project.get("reasons", ""),

            project["name"],
            project["symbol"]
        )

        if existing:

            # UPDATE
            cursor.execute("""
                UPDATE projects SET
                    market_cap = ?,
                    volume_24h = ?,
                    price_change_24h = ?,
                    price_change_7d = ?,

                    score = ?,
                    verdict = ?,
                    confidence = ?,
                    reasons = ?

                WHERE name = ? AND symbol = ?
            """, data)

        else:

            # INSERT
            cursor.execute("""
                INSERT INTO projects (

                    market_cap,
                    volume_24h,
                    price_change_24h,
                    price_change_7d,

                    score,
                    verdict,
                    confidence,
                    reasons,

                    name,
                    symbol
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

        conn.commit()

    except Exception as e:
        print(f"⚠️ DB Error ({project.get('name')}): {e}")
        conn.rollback()

    finally:
        conn.close()

