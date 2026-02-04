
import math
import json
import os
#import openai
from openai import OpenAI
# import hashlib
# import time



# -------------------------
# OPENAI CONFIG
# -------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# openai.api_key = os.getenv("OPENAI_API_KEY")


# -------------------------
# Fallback Scoring Engine
# -------------------------
def fallback_analysis(data):
    market_cap = float(data.get("market_cap", 0) or 0)
    volume = float(data.get("volume_24h", 0) or 0)
    change = float(data.get("price_change_24h", 0) or 0)

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
        "ai_analysis": "Fallback system used",
        "strategy": "Wait for stronger confirmation",
        "risk_warning": "Limited data confidence"
    }


# -------------------------
# Main AI Engine
# -------------------------
def analyze_project(data: dict):
    """
    AI-powered crypto analysis engine
    """

    try:
        prompt = f"""
You are a professional crypto investment analyst.

Analyze this crypto asset using market data.

Return ONLY valid JSON with these fields:

score (0-100 number)
verdict (STRONG BUY / BUY / HOLD / AVOID)
confidence (0-1)
reasons (short explanation)
ai_analysis (detailed reasoning)
strategy (trading/investment strategy)
risk_warning (main risks)

DATA:
Name: {data.get("name")}
Symbol: {data.get("symbol")}
Market Cap: {data.get("market_cap")}
24h Volume: {data.get("volume_24h")}
24h Change: {data.get("price_change_24h")}
7d Change: {data.get("price_change_7d")}
Rank: {data.get("market_cap_rank")}
"""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior crypto analyst AI."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=600
        )

        raw = response["choices"][0]["message"]["content"]

        result = json.loads(raw)

        # Validate minimum fields
        required = ["score", "verdict", "confidence"]

        for field in required:
            if field not in result:
                raise ValueError("Missing field " + field)

        return result


    except Exception as e:
        print("⚠️ AI Engine Error:", e)

        # Safety fallback (never crash Railway)
        return fallback_analysis(data)