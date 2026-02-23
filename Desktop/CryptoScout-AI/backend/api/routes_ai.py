
from fastapi import APIRouter
from services.explanation_service import generate_trending_explanation

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/explain/{symbol}")
def explain(symbol: str):
    return generate_trending_explanation(symbol)