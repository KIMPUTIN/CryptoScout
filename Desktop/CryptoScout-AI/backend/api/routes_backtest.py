
from fastapi import APIRouter
from services.backtest_service import backtest_top_n

router = APIRouter(prefix="/backtest", tags=["Backtest"])


@router.get("/")
def run_backtest(days_ago: int = 7, top_n: int = 10):
    return backtest_top_n(days_ago, top_n)
