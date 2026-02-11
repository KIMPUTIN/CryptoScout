
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import (
    init_db,
    get_all_projects,
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist
)

from recommendation_engine import recommend
from llm_engine import generate_analysis
from ranking import (
    get_short_term,
    get_long_term,
    get_low_risk,
    get_high_growth
)

from scheduler import start_scheduler
from auth import get_current_user

app = FastAPI()

# -------------------
# CORS
# -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------
# Startup
# -------------------
@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()

# -------------------
# Health
# -------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------
# Projects
# -------------------
@app.get("/projects")
def api_projects():
    projects = get_all_projects()
    projects.sort(key=lambda x: x["score"], reverse=True)
    return projects

# -------------------
# Rankings
# -------------------
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

# -------------------
# Recommendation + AI
# -------------------
@app.get("/recommend/{profile}")
def get_recommendation(profile: str):
    recs = recommend(profile)
    ai = generate_analysis(profile, recs)
    return {
        "profile": profile,
        "recommendations": recs,
        "ai_analysis": ai
    }

# -------------------
# Protected Scan
# -------------------
@app.post("/scan/trigger")
def trigger_scan(user=Depends(get_current_user)):
    from scanner import scan_coingecko
    scan_coingecko()
    return {"status": "scan started"}

# -------------------
# Watchlist
# -------------------
@app.post("/watchlist/add/{symbol}")
def api_add_watchlist(symbol: str, user=Depends(get_current_user)):
    projects = get_all_projects()
    project = next((p for p in projects if p["symbol"] == symbol.upper()), None)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    add_to_watchlist(user["id"], project)
    return {"status": "added", "symbol": symbol}

@app.get("/watchlist")
def api_get_watchlist(user=Depends(get_current_user)):
    return get_watchlist(user["id"])

@app.delete("/watchlist/{symbol}")
def api_remove_watchlist(symbol: str, user=Depends(get_current_user)):
    remove_from_watchlist(user["id"], symbol)
    return {"status": "removed", "symbol": symbol}
