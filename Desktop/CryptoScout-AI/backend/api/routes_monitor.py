
# backend/api/routes_monitor.py

from fastapi import APIRouter
from datetime import datetime

from services.scanner_service import get_scan_status
from services.ai_service import ai_engine_health
from services.market_service import breaker
from services.market_service import api_tracker



router = APIRouter(tags=["Monitor"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/monitor")
def monitor():

    scan_info = get_scan_status()

    overall_status = "healthy"

    if scan_info["scanner"]["last_result"] == "FAILED":
        overall_status = "degraded"

    if scan_info["scanner"]["failure_count"] > 3:
        overall_status = "critical"

    if api_tracker.snapshot()["calls_last_hour"] > 80:
        logger.warning("Approaching API budget limit")


    return {
        "overall_status": overall_status,
        "scanner": scan_info["scanner"],
        "api_failures": scan_info["api_failures"],
        "ai_engine": ai_engine_health(),
        "timestamp": datetime.utcnow().isoformat(),
        "market_circuit": breaker.snapshot(),
        "api_usage": api_tracker.snapshot()
    }
