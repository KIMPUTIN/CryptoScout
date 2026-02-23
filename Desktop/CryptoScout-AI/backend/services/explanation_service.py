
import logging
from typing import Dict
from services.ai_service import analyze_project
from database.repository import get_project_by_symbol

logger = logging.getLogger(__name__)


def generate_trending_explanation(symbol: str) -> Dict:

    project = get_project_by_symbol(symbol)

    if not project:
        return {"error": "Project not found"}

    ai_result = analyze_project(project)

    explanation = f"""
{project['name']} ({project['symbol']}) is currently trending due to 
a 24h price movement of {project.get('price_change_24h', 0)}% and 
a 7-day momentum of {project.get('price_change_7d', 0)}%.

AI rating: {ai_result.get('verdict')}
Confidence: {round(ai_result.get('confidence', 0) * 100)}%

Volatility level is assessed as {project.get('price_change_24h')}% 
which indicates {'high speculative activity' if abs(project.get('price_change_24h', 0)) > 8 else 'moderate market stability'}.

Overall outlook: {ai_result.get('strategy')}
"""

    return {
        "symbol": symbol,
        "explanation": explanation.strip()
    }