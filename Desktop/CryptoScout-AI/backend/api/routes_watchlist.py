
# backend/api/routes_watchlist.py

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header

from core.config import JWT_SECRET, JWT_ALGORITHM
from database.repository import (
    get_user_by_id,
    get_all_projects
)
from database.db import get_connection

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


# =============================
# AUTH DEPENDENCY
# =============================

def get_current_user(authorization: str = Header(None)):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = get_user_by_id(payload["user_id"])

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# =============================
# ROUTES
# =============================

@router.post("/add/{symbol}")
def add_watchlist(symbol: str, user=Depends(get_current_user)):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO watchlist (user_id, symbol) VALUES (?, ?)",
        (user["id"], symbol.upper())
    )

    conn.commit()
    conn.close()

    return {"status": "added", "symbol": symbol.upper()}


@router.get("/")
def fetch_watchlist(user=Depends(get_current_user)):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT symbol FROM watchlist WHERE user_id=?",
        (user["id"],)
    )

    rows = cursor.fetchall()
    conn.close()

    return [r["symbol"] for r in rows]


@router.delete("/remove/{symbol}")
def remove_watchlist(symbol: str, user=Depends(get_current_user)):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM watchlist WHERE user_id=? AND symbol=?",
        (user["id"], symbol.upper())
    )

    conn.commit()
    conn.close()

    return {"status": "removed", "symbol": symbol.upper()}
