
# backend/recommendation_engine.py

import math
from database import get_all_projects


# --------------------------------------------------
# USER PROFILES (STRATEGY WEIGHTS)
# --------------------------------------------------

PROFILES = {

    "safe": {
        "fundamental": 0.4,
        "momentum": 0.1,
        "risk": 0.4,
        "ai": 0.1
    },

    "balanced": {
        "fundamental": 0.35,
        "momentum": 0.25,
        "risk": 0.2,
        "ai": 0.2
    },

    "aggressive": {
        "fundamental": 0.25,
        "momentum": 0.4,
        "risk": 0.15,
        "ai": 0.2
    },

    "short-term": {
        "fundamental": 0.2,
        "momentum": 0.5,
        "risk": 0.1,
        "ai": 0.2
    },

    "long-term": {
        "fundamental": 0.45,
        "momentum": 0.15,
        "risk": 0.25,
        "ai": 0.15
    }
}


# --------------------------------------------------
# NORMALIZATION
# --------------------------------------------------

def _normalize(val, min_val, max_val):

    if max_val == min_val:
        return 0.5

    return (val - min_val) / (max_val - min_val)


# --------------------------------------------------
# COMPONENT SCORING
# --------------------------------------------------

def _fundamental(p):

    mc = p.get("market_cap", 0)
    vol = p.get("volume_24h", 0)

    mc_score = math.log10(mc + 1)
    vol_score = math.log10(vol + 1)

    return (mc_score + vol_score) / 2


def _momentum(p):

    d1 = p.get("price_change_24h", 0)
    d7 = p.get("price_change_7d", 0)

    return (d1 * 0.6) + (d7 * 0.4)


def _risk(p):

    vol = abs(p.get("price_change_24h", 0))
    conf = p.get("confidence", 0)

    risk = (vol * 0.7) + ((1 - conf) * 0.3)

    return max(0, risk)


def _ai_score(p):

    return p.get("confidence", 0) * 100


# --------------------------------------------------
# MAIN RECOMMENDER
# --------------------------------------------------

def recommend(profile="balanced", top_n=5):

    projects = get_all_projects()

    if not projects:
        return []

    if profile not in PROFILES:
        profile = "balanced"

    weights = PROFILES[profile]


    # Collect raw values
    fundamentals = [_fundamental(p) for p in projects]
    momentum = [_momentum(p) for p in projects]
    risks = [_risk(p) for p in projects]
    ai_scores = [_ai_score(p) for p in projects]


    f_min, f_max = min(fundamentals), max(fundamentals)
    m_min, m_max = min(momentum), max(momentum)
    r_min, r_max = min(risks), max(risks)
    a_min, a_max = min(ai_scores), max(ai_scores)


    ranked = []


    for i, p in enumerate(projects):

        f = _normalize(fundamentals[i], f_min, f_max)
        m = _normalize(momentum[i], m_min, m_max)
        r = 1 - _normalize(risks[i], r_min, r_max)  # invert
        a = _normalize(ai_scores[i], a_min, a_max)


        final = (
            f * weights["fundamental"] +
            m * weights["momentum"] +
            r * weights["risk"] +
            a * weights["ai"]
        )


        ranked.append({
            "name": p["name"],
            "symbol": p["symbol"],
            "final_score": round(final, 4),
            "score": p["score"],
            "confidence": p["confidence"],
            "reasons": p["reasons"]
        })


    ranked.sort(key=lambda x: x["final_score"], reverse=True)

    return ranked[:top_n]
