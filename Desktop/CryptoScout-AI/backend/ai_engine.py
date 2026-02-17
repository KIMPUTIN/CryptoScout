
# backend/ai_engine.py

import math
import json
import os
import time
import re
import logging
from typing import Dict, Any

from openai import OpenAI


# =====================================================
# LOGGING
# =====================================================

logger = logging.getLogger("AI_ENGINE")


# =====================================================
# CONFIG
# =====================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set — AI will fallback.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MAX_RETRIES = 3
AI_TIMEOUT = 30


# =====================================================
# FALLBACK ENGINE
# =====================================================

def fallback_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic scoring fallback if AI fails.
    Safe and guaranteed to return structured data.
    """

    try:
        market_cap = float(data.get("market_cap") or 0)
        volume = float(data.get("volume_24h") or 0)
        change = float(data.get("price_change_24h") or 0)

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
            "confidence": round(score / 100, 2),
            "reasons": "Rule-based fallback analysis",
            "ai_analysis": "Fallback system used",
            "strategy": "Wait for stronger confirmation",
            "risk_warning": "Limited AI availability"
        }

    except Exception as e:
        logger.error("Fallback failed: %s", e)

        return {
            "score": 0,
            "verdict": "HOLD",
            "confidence": 0.1,
            "reasons": "System error",
            "ai_analysis": "Emergency fallback",
            "strategy": "Do not trade",
            "risk_warning": "System instability"
        }


# =====================================================
# JSON EXTRACTION
# =====================================================

def _extract_json(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty AI response")

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found")

    return json.loads(match.group(0))


# =====================================================
# MAIN AI ANALYSIS
# =====================================================

def analyze_project(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Production-safe AI analysis.
    Always returns valid structured data.
    """

    if not client:
        return fallback_analysis(data)

    prompt = f"""
You are a professional crypto investment analyst.

Return ONLY valid JSON.

FORMAT:
{{
  "score": number (0-100),
  "verdict": "STRONG BUY" | "BUY" | "HOLD" | "AVOID",
  "confidence": number (0-1),
  "reasons": string,
  "ai_analysis": string,
  "strategy": string,
  "risk_warning": string
}}

DATA:
Name: {data.get("name")}
Symbol: {data.get("symbol")}
Market Cap: {data.get("market_cap")}
24h Volume: {data.get("volume_24h")}
24h Change: {data.get("price_change_24h")}
7d Change: {data.get("price_change_7d")}
Rank: {data.get("market_cap_rank")}
"""

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            logger.info("AI attempt %s", attempt)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Return ONLY JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500,
                timeout=AI_TIMEOUT
            )

            raw = response.choices[0].message.content.strip()

            result = _extract_json(raw)

            # Validation
            required = [
                "score",
                "verdict",
                "confidence",
                "reasons",
                "ai_analysis",
                "strategy",
                "risk_warning"
            ]

            for field in required:
                if field not in result:
                    raise ValueError(f"Missing field: {field}")

            # Normalize values
            result["score"] = max(0, min(100, float(result["score"])))
            result["confidence"] = max(0, min(1, float(result["confidence"])))

            logger.info("AI success")

            return result

        except Exception as e:
            logger.warning("AI attempt %s failed: %s", attempt, e)
            time.sleep(1.5)

    logger.error("AI failed after retries — fallback engaged")
    return fallback_analysis(data)


# =====================================================
# HEALTH CHECK
# =====================================================

def ai_engine_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "openai_key_loaded": bool(OPENAI_API_KEY),
        "engine": "CryptoScout AI v2.0"
    }
