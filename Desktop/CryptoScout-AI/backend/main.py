

from fastapi import Header, HTTPException
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from recommendation_engine import recommend
from llm_engine import generate_analysis
from database import init_db, seed_test_data, get_all_projects, DB_NAME
from scheduler import start_scheduler
from ranking import (
    get_short_term,
    get_long_term,
    get_low_risk,
    get_high_growth
)


ADMIN_KEY = os.getenv("ADMIN_KEY")


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

    if os.getenv("RESET_DB") == "true":

        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
            print("🔥 Database reset")

        else:
            print("ℹ️ No database to reset")

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
def trigger_scan(x_admin_key: str = Header(None)):

    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

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


#@app.get("/recommend/{profile}")
#def get_recommendation(profile: str):

#    data = recommend(profile)

#    return {
#        "profile": profile,
#        "recommendations": data
#    }


@app.get("/recommend/{profile}")
def get_recommendation(profile: str):

    recs = recommend(profile)

    ai = generate_analysis(profile, recs)

    return {
        "profile": profile,
        "recommendations": recs,
        "ai_analysis": ai
    }
