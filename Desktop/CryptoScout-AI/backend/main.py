

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import scan_projects
from scoring import score_project
from database import SessionLocal, init_db
from models import Project

app = FastAPI()
scheduler = BackgroundScheduler()
# Added line 14 to 19 ##################
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def job():
    db = SessionLocal()
    projects = scan_projects()

    for p in projects:
        score, verdict, reasons = score_project(p)
        project = Project(
            name=p["name"],
            symbol=p["symbol"],
            website=p["website"],
            score=score,
            verdict=verdict,
            reasons=reasons
        )
        db.add(project)

    db.commit()
    db.close()

@app.on_event("startup")
def start():
    init_db()
    scheduler.add_job(job, "interval", hours=1)
    scheduler.start()

@app.get("/projects")
def get_projects():
    db = SessionLocal()
    return db.query(Project).all()

# Added line 52 to line 54 at the bottom ##################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

