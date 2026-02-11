



import sqlite3
import os
from datetime import datetime


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

  # Users table (Google OAuth)
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  google_id TEXT UNIQUE,
  email TEXT,
  name TEXT,
  picture TEXT,
  created_at TEXT
)
""")


  # Auto-migrate missing columns (safe in production)
  columns = {
  "market_cap": "REAL",
  "volume_24h": "REAL",
  "price_change_24h": "REAL",
  "price_change_7d": "REAL",
  "confidence": "REAL",

  # Phase 2 signals
  "sentiment_score": "REAL",
  "social_volume": "INTEGER",
  "trend_score": "REAL",
  "last_updated": "TEXT",
  "news_volume": "INTEGER"
  }

  #-----------
  # Watchlist table
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    symbol TEXT,
    name TEXT,
    score_at_add REAL,
    sentiment_at_add REAL,
    trend_at_add REAL,
    created_at TEXT
)
""")



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
      reasons,
      sentiment_score,
      social_volume,
      trend_score,
      last_updated,
      news_volume


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


# ---------------------------------------

def add_to_watchlist(user_id, project):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO watchlist (
            user_id,
            symbol,
            name,
            score_at_add,
            sentiment_at_add,
            trend_at_add,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        project.get("symbol"),
        project.get("name"),
        project.get("score"),
        project.get("sentiment_score", 0),
        project.get("trend_score", 0),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_watchlist(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM watchlist
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_from_watchlist(user_id, symbol):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM watchlist
        WHERE user_id = ? AND symbol = ?
    """, (user_id, symbol))

    conn.commit()
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

    from datetime import datetime

    now = datetime.utcnow().isoformat()

    data = (
      project.get("market_cap", 0),
      project.get("volume_24h", 0),
      project.get("price_change_24h", 0),
      project.get("price_change_7d", 0),

      project.get("score", 0),
      project.get("verdict", ""),
      project.get("confidence", 0),
      project.get("reasons", ""),

       # Phase 2 fields
      project.get("sentiment_score", 0),
      project.get("social_volume", 0),
      project.get("trend_score", 0),
      project.get("news_volume", 0),
      now,

      project["name"],
      project["symbol"]
    )

    if existing:

      # UPDATE SQL Querries
      cursor.execute("""
        UPDATE projects SET
          market_cap = ?,
          volume_24h = ?,
          price_change_24h = ?,
          price_change_7d = ?,

          score = ?,
          verdict = ?,
          confidence = ?,
          reasons = ?,

          sentiment_score = ?,
          social_volume = ?,
          trend_score = ?,
          last_updated = ?,
          news_volume = ?

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

          sentiment_score,
          social_volume,
          trend_score,
          last_updated,
          news_volume,

          name,
          symbol
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, data)

    conn.commit()

  except Exception as e:
    print(f"⚠️ DB Error ({project.get('name')}): {e}")
    conn.rollback()

  finally:
    conn.close()


#Create or Get User
def get_or_create_user(google_id, email, name, picture):
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()

  cursor.execute("""
    SELECT * FROM users WHERE google_id = ?
  """, (google_id,))

  existing = cursor.fetchone()

  if existing:
    conn.close()
    return dict(existing)

  from datetime import datetime

  now = datetime.utcnow().isoformat()

  cursor.execute("""
    INSERT INTO users (google_id, email, name, picture, created_at)
    VALUES (?, ?, ?, ?, ?)
  """, (google_id, email, name, picture, now))

  conn.commit()

  cursor.execute("""
    SELECT * FROM users WHERE google_id = ?
  """, (google_id,))

  user = cursor.fetchone()

  conn.close()

  return dict(user)


#Get User by ID
def get_user_by_id(user_id):
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()

  cursor.execute("""
    SELECT * FROM users WHERE id = ?
  """, (user_id,))

  user = cursor.fetchone()
  conn.close()

  if user:
    return dict(user)

  return None
