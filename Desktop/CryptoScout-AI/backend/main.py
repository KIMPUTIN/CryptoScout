
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import get_all_projects

app = FastAPI()

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
