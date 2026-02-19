
from fastapi import APIRouter
from database.repository import get_all_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
def fetch_alerts(limit: int = 50):
    return get_all_alerts(limit)
