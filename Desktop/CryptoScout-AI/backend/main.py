import sys
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Ensure the current directory is in the path for Railway
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import database functions
from database import get_all_projects, init_db

app = FastAPI()
init_db()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    projects = get_all_projects()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "projects": projects}
    )


@app.get("/projects")
def api_projects():
    return get_all_projects()
