


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)



import sqlite3

DB_NAME = "cryptoscout.db"


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
