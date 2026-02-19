
# backend/services/ranking_service.py

import logging
from datetime import datetime
from typing import List, Dict, Optional

from core.config import RANKING_CACHE_DURATION
from database.repository import get_all_projects
from core.redis_client import cache_get, cache_set


logger = logging.getLogger(__name__)

"""_cache = {
    "data": None,
    "timestamp": None
}
"""

# =====================================================
# CORE METRICS
# =====================================================

def compute_trend_momentum(project: Dict) -> float:
    change_24h = float(project.get("price_change_24h") or 0)
    change_7d = float(project.get("price_change_7d") or 0)
    return round((0.6 * change_7d + 0.4 * change_24h) / 100, 4)


def compute_volatility_heat(project: Dict) -> str:
    change = abs(float(project.get("price_change_24h") or 0))

    if change > 15:
        return "EXTREME"
    elif change > 8:
        return "HIGH"
    elif change > 3:
        return "MODERATE"
    else:
        return "LOW"


# =====================================================
# RISK PROFILE SCORING
# =====================================================

def compute_combined_score(project: Dict, profile: str = "balanced") -> float:

    market_cap = float(project.get("market_cap") or 0)
    ai_score = float(project.get("ai_score") or 0) / 100
    sentiment = float(project.get("sentiment_score") or 0)
    volatility = abs(float(project.get("price_change_24h") or 0)) / 100
    momentum = compute_trend_momentum(project)

    if profile == "aggressive":
        score = (
            0.35 * momentum +
            0.25 * ai_score +
            0.20 * sentiment +
            0.20 * volatility
        )

    elif profile == "conservative":
        stability_bonus = min(market_cap / 1_000_000_000, 1)
        score = (
            0.40 * stability_bonus +
            0.25 * sentiment +
            0.20 * ai_score -
            0.25 * volatility
        )

    else:  # balanced
        score = (
            0.30 * momentum +
            0.20 * ai_score +
            0.20 * sentiment -
            0.15 * volatility
        )

    return round(score, 4)


# =====================================================
# RANKING ENGINE
# =====================================================

def _build_rankings(profile: str = "balanced") -> List[Dict]:

    projects = get_all_projects()
    ranked = []

    for project in projects:
        score = compute_combined_score(project, profile)

        project["combined_score"] = score
        project["volatility_heat"] = compute_volatility_heat(project)
        project["trend_momentum"] = compute_trend_momentum(project)

        # ✅ serialize EACH project
        ranked.append(serialize_project_summary(project))

    ranked.sort(key=lambda x: x["combined_score"], reverse=True)

    logger.info("Rankings rebuilt (%s projects)", len(ranked))

    return ranked



# =====================================================
# CACHE ACCESS
# =====================================================

def get_rankings(
    profile: str = "balanced",
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:

    cached = cache_get(f"rankings:{profile}")
    if not cached:
        data = _build_rankings(profile)
        cache_set(f"rankings:{profile}", data, 300)
    else:
        data = cached

    return data[offset:offset + limit]




# =====================================================
# PERSONALIZATION
# =====================================================

def personalize_rankings(
    rankings: List[Dict],
    user_preferences: Optional[List[str]] = None
) -> List[Dict]:

    if not user_preferences:
        return rankings

    for project in rankings:
        if project["symbol"] in user_preferences:
            project["combined_score"] += 0.1

    rankings.sort(key=lambda x: x["combined_score"], reverse=True)
    return rankings


# =====================================================
# FILTERED VIEWS
# =====================================================

def get_short_term(
    profile: str = "balanced",
    limit: int = 20,
    offset: int = 0
):
    return get_rankings(profile, limit, offset)


def get_long_term(
    profile: str = "balanced",
    limit: int = 20,
    offset: int = 0
):
    data = get_rankings(profile)
    data = sorted(
        data,
        key=lambda x: x.get("market_cap", 0),
        reverse=True
    )
    return data[offset:offset + limit]


def get_low_risk(
    profile: str = "balanced",
    limit: int = 20,
    offset: int = 0
):
    data = get_rankings(profile)
    data = sorted(
        data,
        key=lambda x: abs(x.get("price_change_24h", 0))
    )
    return data[offset:offset + limit]


def get_high_growth(
    profile: str = "balanced",
    limit: int = 20,
    offset: int = 0
):
    data = get_rankings(profile)
    data = sorted(
        data,
        key=lambda x: x.get("price_change_7d", 0),
        reverse=True
    )
    return data[offset:offset + limit]


def serialize_project_summary(project: Dict) -> Dict:
    return {
        "symbol": project["symbol"],
        "name": project["name"],
        "current_price": project.get("current_price"),
        "combined_score": project["combined_score"],
        "volatility_heat": project["volatility_heat"],
        "trend_momentum": project["trend_momentum"],
        "ai_score": project.get("ai_score")
    }
