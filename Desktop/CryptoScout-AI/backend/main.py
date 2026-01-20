import os
print("CURRENT WORKING DIRECTORY:", os.getcwd())
print("FILES IN CWD:", os.listdir(os.getcwd()))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import init_db, seed_test_data, get_all_projects

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("BASE_DIR:", BASE_DIR)
print("FILES IN BASE_DIR:", os.listdir(BASE_DIR))

app = FastAPI()

# Static files
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

print("STATIC DIR:", static_dir)
print("STATIC DIR EXISTS:", os.path.exists(static_dir))
if os.path.exists(static_dir):
    print("FILES IN STATIC DIR:", os.listdir(static_dir))



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
