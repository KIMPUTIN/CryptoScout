
import math
import json
import os
from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------
# OPENAI CONFIG
# -------------------------

# openai.api_key = os.getenv("OPENAI_API_KEY")


# -------------------------
# SYSTEM PROMPT
# -------------------------

SYSTEM_PROMPT = """
You are CryptoScout AI.

You analyze crypto projects using market data.

Your task:
- Evaluate risk
- Evaluate growth potential
- Evaluate stability
- Give clear investment advice

Return ONLY valid JSON with:

score (0-100)
verdict (STRONG BUY, BUY, HOLD, AVOID)
confidence (0-1)
reasons (string)
"""

# -------------------------
# SAFE PARSER
# -------------------------

def safe_parse_json(text):

    try:
        return json.loads(text)
    except:
        print("⚠️ AI returned invalid JSON")
        return {
            "ai_analysis": "Analysis unavailable",
            "summary": "N/A",
            "strengths": [],
            "weaknesses": [],
            "risk_warning": "Unknown risk",
            "strategy": "No strategy",
            "ai_score": 50,
            "confidence": 0.5
        }


# -------------------------
# PROMPT BUILDER
# -------------------------

def build_prompt(p):

    return f"""
Analyze this crypto project carefully.

PROJECT DATA:
Name: {p['name']}
Symbol: {p['symbol']}
Market Cap: {p['market_cap']}
24h Volume: {p['volume_24h']}
24h Change: {p['price_change_24h']}%
7d Change: {p['price_change_7d']}%
Market Rank: {p['market_cap_rank']}

Evaluate:

1. Market strength
2. Liquidity
3. Trend
4. Risk
5. Long-term potential

Return ONLY valid JSON:

{{
  "ai_analysis": "...",
  "summary": "...",
  "strengths": ["...","..."],
  "weaknesses": ["...","..."],
  "risk_warning": "...",
  "strategy": "...",
  "ai_score": 0-100,
  "confidence": 0.0-1.0
}}
"""
    

# -------------------------
# SAFE NUMBER
# -------------------------

def safe(value, default=0):

    if value is None:
        return default

    try:
        return float(value)
    except:
        return default


# -------------------------
# TECHNICAL SCORE
# -------------------------

def technical_score(p):

    score = 0

    # Liquidity
    if p["volume_24h"] > 100_000_000:
        score += 20
    elif p["volume_24h"] > 20_000_000:
        score += 10

    # Market cap
    if p["market_cap"] > 10_000_000_000:
        score += 20
    elif p["market_cap"] > 1_000_000_000:
        score += 10

    # Momentum
    if p["price_change_7d"] > 15:
        score += 15
    elif p["price_change_7d"] > 5:
        score += 8

    # Stability
    if abs(p["price_change_24h"]) < 5:
        score += 10

    return min(score, 60)


# -------------------------
# MAIN ANALYZER
# -------------------------

def analyze_project(data: dict):

    user_prompt = f"""
Analyze this crypto project:

Name: {data.get("name")}
Symbol: {data.get("symbol")}
Market Cap: {data.get("market_cap")}
Volume 24h: {data.get("volume_24h")}
Price Change 24h: {data.get("price_change_24h")}
Price Change 7d: {data.get("price_change_7d")}
Rank: {data.get("market_cap_rank")}

Return JSON only.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content

        result = json.loads(content)

        return result

    except Exception as e:

        print("❌ AI ERROR:", e)

        # Fallback (never crash scanner)
        return {
            "score": 50,
            "verdict": "HOLD ⚠️",
            "confidence": 0.5,
            "reasons": "AI analysis unavailable"
        }


    # -------------------------
    # AI Analysis
    # -------------------------

    prompt = build_prompt(project)

    try:

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            timeout=30
        )

        raw = response.choices[0].message.content

        ai_result = safe_parse_json(raw)

    except Exception as e:

        print("⚠️ AI ERROR:", e)

        ai_result = safe_parse_json("")


    # -------------------------
    # Technical Score
    # -------------------------

    tech = technical_score(project)


    # -------------------------
    # Hybrid Score
    # -------------------------

    final_score = round(
        (ai_result["ai_score"] * 0.6) + (tech * 0.4),
        2
    )


    # -------------------------
    # Verdict
    # -------------------------

    if final_score >= 75:
        verdict = "STRONG BUY 🚀"
    elif final_score >= 60:
        verdict = "BUY ✅"
    elif final_score >= 45:
        verdict = "HOLD ⚠️"
    else:
        verdict = "AVOID ❌"


    # -------------------------
    # Return Full Profile
    # -------------------------

    return {
        "score": final_score,
        "verdict": verdict,
        "confidence": ai_result["confidence"],

        "ai_analysis": ai_result["ai_analysis"],
        "summary": ai_result["summary"],
        "strengths": ai_result["strengths"],
        "weaknesses": ai_result["weaknesses"],
        "risk_warning": ai_result["risk_warning"],
        "strategy": ai_result["strategy"],
    }


