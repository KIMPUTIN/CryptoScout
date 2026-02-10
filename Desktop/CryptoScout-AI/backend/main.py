

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
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
from database import get_or_create_user
from database import get_user_by_id
from fastapi import Header, HTTPException
from fastapi import Depends, HTTPException
from database import add_to_watchlist, get_watchlist, remove_from_watchlist
from auth import get_current_user
from database import get_all_projects



ADMIN_KEY = os.getenv("ADMIN_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


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


@app.post("/auth/google")
async def google_login(payload: dict):

  token = payload.get("token")

  try:
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

    session_token = jwt.encode(
      {"user_id": user["id"]},
      JWT_SECRET,
      algorithm="HS256"
    )

    return {
      "user": user,
      "token": session_token
    }

  except Exception as e:
    return {"error": str(e)}


@app.get("/me")
def get_me(authorization: str = Header(None)):

  if not authorization:
    raise HTTPException(status_code=401)

  token = authorization.replace("Bearer ", "")

  try:
    data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    user = get_user_by_id(data["user_id"])
    return user
  except:
    raise HTTPException(status_code=401)

# --------------------------------------------------
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
