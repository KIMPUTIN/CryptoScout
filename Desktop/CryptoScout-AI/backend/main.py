
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import sentry_sdk
import os

from core.config import APP_NAME, ALLOWED_ORIGINS
from core.logging_config import setup_logging
from database.db import init_db
from scheduler import start_scheduler

from api.routes_auth import router as auth_router
from api.routes_rankings import router as rankings_router
from api.routes_watchlist import router as watchlist_router
from api.routes_monitor import router as monitor_router
from api.routes_backtest import router as backtest_router
from api.routes_alerts import router as alerts_router
from api.routes_ws import router as ws_router


# =====================================================
# LOGGING FIRST
# =====================================================

setup_logging()


# =====================================================
# CREATE APP (MUST COME EARLY)
# =====================================================

app = FastAPI(title=APP_NAME)


# =====================================================
# SENTRY
# =====================================================

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0
    )


# =====================================================
# MIDDLEWARE
# =====================================================

app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# ROUTERS
# =====================================================

app.include_router(auth_router)
app.include_router(rankings_router)
app.include_router(watchlist_router)
app.include_router(monitor_router)
app.include_router(backtest_router)
app.include_router(alerts_router)
app.include_router(ws_router)


# =====================================================
# STARTUP
# =====================================================

@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()
