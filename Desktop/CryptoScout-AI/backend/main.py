

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import scan_projects
from scoring import score_project
from database import SessionLocal, init_db
from models import Project

app = FastAPI()
scheduler = BackgroundScheduler()

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
