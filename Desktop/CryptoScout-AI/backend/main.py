
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_all_projects
from scheduler import start_scheduler
from ranking import (
    get_short_term,
    get_long_term,
    get_low_risk,
    get_high_growth
)


app = FastAPI()


# ✅ Allow frontend access (TEMP: open for debug)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Startup
@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()


# ✅ API only
@app.get("/projects")
def api_projects():
    projects = get_all_projects()

    projects.sort(key=lambda x: x["score"], reverse=True)

    return projects


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan/trigger")
@app.get("/scan/trigger")
def trigger_scan():
    from scanner import scan_coingecko

    scan_coingecko()

    projects = get_all_projects()

    return {
        "status": "success",
        "total_projects": len(projects)
    }

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
