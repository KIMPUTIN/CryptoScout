import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import init_db, seed_test_data, get_all_projects

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Static files
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)


@app.on_event("startup")
def startup_event():
    init_db()
    seed_test_data()


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


@app.get("/health")
def health():
    """Lightweight runtime check useful for deployments."""
    css_path = os.path.join(static_dir, "style.css")
    return {
        "ok": True,
        "base_dir": BASE_DIR,
        "static_dir": static_dir,
        "style_css_exists": os.path.exists(css_path),
    }
