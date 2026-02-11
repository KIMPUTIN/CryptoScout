
# backend/main.py

import os
import jwt
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from database import (
    init_db,
    get_all_projects,
    get_or_create_user,
    get_user_by_id,
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist
)

from ranking import (
    get_short_term,
    get_long_term,
    get_low_risk,
    get_high_growth
)

from scheduler import start_scheduler


# ==========================================
# CONFIG
# ==========================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key")

# ==========================================
# FASTAPI INIT
# ==========================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# STARTUP
# ==========================================

@app.on_event("startup")
def startup_event():
    print("🚀 Starting CryptoScout Backend...")
    init_db()
    start_scheduler()
    print("✅ Backend Ready")


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():
    return {"status": "ok"}


# ==========================================
# RANKINGS
# ==========================================

@app.get("/projects")
def projects():
    return get_all_projects()


@app.get("/rankings/short-term")
def short_term():
    return get_short_term()


@app.get("/rankings/long-term")
def long_term():
    return get_long_term()


@app.get("/rankings/low-risk")
def low_risk():
    return get_low_risk()


@app.get("/rankings/high-growth")
def high_growth():
    return get_high_growth()


# ==========================================
# GOOGLE AUTH
# ==========================================

@app.post("/auth/google")
async def auth_google(payload: dict):
    try:
        token = payload.get("token")

        if not token:
            raise HTTPException(status_code=400, detail="Token missing")

        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        google_id = idinfo["sub"]
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        user = get_or_create_user(
            google_id,
            email,
            name,
            picture
        )

        jwt_token = jwt.encode(
            {
                "user_id": user["id"],
                "exp": datetime.utcnow() + timedelta(days=7)
            },
            JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "token": jwt_token,
            "user": user
        }

    except Exception as e:
        print("❌ Google Auth Error:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")


# ==========================================
# AUTH DEPENDENCY
# ==========================================

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth header")

    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")

        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==========================================
# WATCHLIST
# ==========================================

@app.post("/watchlist/add/{symbol}")
def add_watchlist(symbol: str, user=Depends(get_current_user)):
    projects = get_all_projects()

    project = next(
        (p for p in projects if p["symbol"] == symbol.upper()),
        None
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    add_to_watchlist(user["id"], project)

    return {"status": "added", "symbol": symbol.upper()}


@app.get("/watchlist")
def fetch_watchlist(user=Depends(get_current_user)):
    return get_watchlist(user["id"])


@app.delete("/watchlist/remove/{symbol}")
def delete_watchlist(symbol: str, user=Depends(get_current_user)):
    remove_from_watchlist(user["id"], symbol.upper())
    return {"status": "removed", "symbol": symbol.upper()}
