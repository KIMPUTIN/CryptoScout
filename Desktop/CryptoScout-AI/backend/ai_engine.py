
# backend/ai_engine.py

import math
import json
import os
import time
import re
import logging

from openai import OpenAI


# -------------------------------------------------
# LOGGING CONFIG (Railway Friendly)
# -------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AI_ENGINE] %(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# -------------------------------------------------
# OPENAI CONFIG
# -------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set! AI will fallback.")

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------
# FALLBACK SCORING ENGINE (UNCHANGED CORE LOGIC)
# -------------------------------------------------

def fallback_analysis(data: dict) -> dict:
    """
    Rule-based scoring when AI is unavailable
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
            verdict = "STRONG BUY 🚀"
        elif score >= 60:
            verdict = "BUY ✅"
        elif score >= 45:
            verdict = "HOLD ⚠️"
        else:
            verdict = "AVOID ❌"

        return {
            "score": score,
            "verdict": verdict,
            "confidence": round(score / 100, 2),
            "reasons": "Rule-based fallback analysis",
            "ai_analysis": "Fallback system used due to AI unavailability",
            "strategy": "Wait for stronger confirmation",
            "risk_warning": "Limited data confidence"
        }

    except Exception as e:

        logger.error("Fallback failed: %s", e)

        # Absolute emergency return
        return {
            "score": 0,
            "verdict": "HOLD ⚠️",
            "confidence": 0.1,
            "reasons": "System error",
            "ai_analysis": "Emergency fallback",
            "strategy": "Do not trade",
            "risk_warning": "System instability"
        }


# -------------------------------------------------
# JSON EXTRACTION UTILITY
# -------------------------------------------------

def _extract_json(text: str) -> dict:
    """
    Safely extract JSON object from AI output
    """

    if not text:
        raise ValueError("Empty AI response")

    # Find JSON block inside text
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found")

    json_text = match.group(0)

    return json.loads(json_text)


# -------------------------------------------------
# MAIN AI ENGINE
# -------------------------------------------------

def analyze_project(data: dict) -> dict:
    """
    AI-powered crypto analysis engine
    Safe, retryable, scalable
    """

    MAX_RETRIES = 3

    prompt = f"""
You are a professional crypto investment analyst.

You MUST return ONLY a valid JSON object.

Do NOT add explanations.

Use this exact format:

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

    # If no key → skip AI
    if not OPENAI_API_KEY:
        logger.warning("Missing API key → fallback")
        return fallback_analysis(data)


    for attempt in range(1, MAX_RETRIES + 1):

        try:

            logger.info("AI analysis attempt %s", attempt)

            response = client.chat.completions.create(

                model="gpt-4o-mini",

                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior crypto analyst. Return ONLY JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2,
                max_tokens=600,
                timeout=30
            )

            raw = response.choices[0].message.content.strip()

            logger.debug("Raw AI output: %s", raw[:300])

            result = _extract_json(raw)


            # -----------------------------------------
            # Validate Output
            # -----------------------------------------

            required_fields = [
                "score",
                "verdict",
                "confidence",
                "reasons",
                "ai_analysis",
                "strategy",
                "risk_warning"
            ]

            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing field: {field}")


            # Normalize Values
            result["score"] = float(result["score"])
            result["confidence"] = float(result["confidence"])


            # Clamp ranges
            result["score"] = max(0, min(100, result["score"]))
            result["confidence"] = max(0, min(1, result["confidence"]))


            logger.info("AI analysis successful")

            return result


        except Exception as e:

            logger.warning(
                "AI attempt %s failed: %s",
                attempt,
                str(e)
            )

            time.sleep(1.5)


    # -------------------------------------------------
    # Total Failure → Fallback
    # -------------------------------------------------

    logger.error("AI failed after %s attempts → fallback", MAX_RETRIES)

    return fallback_analysis(data)


# -------------------------------------------------
# OPTIONAL: Health Check (for Railway / Monitoring)
# -------------------------------------------------

def ai_engine_health() -> dict:
    """
    Health check endpoint helper
    """

    return {
        "status": "ok",
        "openai_key": bool(OPENAI_API_KEY),
        "engine": "CryptoScout AI v1.0"
    }
