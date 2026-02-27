
from fastapi import APIRouter, Depends
from api.dependencies import require_pro
from services.explanation_service import generate_trending_explanation
from services.ai_service import analyze_project  # adjust if different
from models.schemas import AIRequest  # adjust if your schema path differs

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/explain/{symbol}")
def explain(symbol: str): #, user=Depends(require_pro)): ------
    return generate_trending_explanation(symbol)


@router.post("/analyze")
async def analyze(request: AIRequest, user=Depends(require_pro)):
    return analyze_project(request.symbol)
    