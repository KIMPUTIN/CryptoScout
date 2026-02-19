
# backend/services/ai_service.py

import math
import logging
from typing import Dict, Any

from openai import OpenAI
from core.config import OPENAI_API_KEY, AI_MODEL, AI_TIMEOUT, AI_MAX_RETRIES

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# =====================================================
# QUALIFICATION FILTER
# =====================================================

def qualifies_for_ai(project: Dict[str, Any]) -> bool:
    """
    Determine whether project is worth AI analysis.
    """

    try:
        market_cap = float(project.get("market_cap") or 0)
        volume = float(project.get("volume_24h") or 0)
        change_24h = abs(float(project.get("price_change_24h") or 0))

        if market_cap < 50_000_000:
            return False

        if volume < 5_000_000:
            return False

        if change_24h < 2:
            return False

        return True

    except Exception:
        return False


# =====================================================
# FALLBACK ENGINE
# =====================================================

def fallback_analysis(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic fallback scoring.
    """

    market_cap = float(project.get("market_cap") or 0)
    volume = float(project.get("volume_24h") or 0)
    change = float(project.get("price_change_24h") or 0)

    score = min(
        math.log10(market_cap + 1) * 15 +
        math.log10(volume + 1) * 12 +
        abs(change) * 1.5,
        100
    )

    score = round(score, 2)

    if score >= 75:
        verdict = "STRONG BUY"
    elif score >= 60:
        verdict = "BUY"
    elif score >= 45:
        verdict = "HOLD"
    else:
        verdict = "AVOID"

    return {
        "score": score,
        "verdict": verdict,
        "confidence": round(score / 100, 2)
    }


# =====================================================
# AI ANALYSIS
# =====================================================

def analyze_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safe AI analysis with fallback.
    Only call this from scheduler.
    """

    if not client:
        return fallback_analysis(project)

    prompt = f"""
Return ONLY JSON with:
score (0-100),
verdict (STRONG BUY, BUY, HOLD, AVOID),
confidence (0-1).

DATA:
Name: {project.get("name")}
Symbol: {project.get("symbol")}
Market Cap: {project.get("market_cap")}
24h Volume: {project.get("volume_24h")}
24h Change: {project.get("price_change_24h")}
7d Change: {project.get("price_change_7d")}
Rank: {project.get("market_cap_rank")}
"""

    for attempt in range(AI_MAX_RETRIES):

        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200,
                timeout=AI_TIMEOUT,
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content

            parsed = eval(result) if isinstance(result, str) else result

            score = max(0, min(100, float(parsed["score"])))
            confidence = max(0, min(1, float(parsed["confidence"])))

            return {
                "score": score,
                "verdict": parsed["verdict"],
                "confidence": confidence
            }

        except Exception as e:
            logger.warning("AI attempt failed: %s", e)

    logger.error("AI failed — using fallback")
    return fallback_analysis(project)


# =====================================================
# HEALTH
# =====================================================

def ai_engine_health():
    return {
        "status": "ok" if OPENAI_API_KEY else "degraded",
        "openai_key_loaded": bool(OPENAI_API_KEY),
        "engine": "CryptoScout AI"
    }


def generate_summary(project: Dict) -> str:

    if not client:
        return "AI summary unavailable."

    prompt = f"""
Explain briefly why {project['name']} ({project['symbol']}) 
is trending based on:

Market Cap
24h Change
7d Change
Volume
AI Score

Keep it under 100 words.
"""

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150,
            timeout=15
        )

        return response.choices[0].message.content.strip()

    except:
        return "AI summary unavailable."
