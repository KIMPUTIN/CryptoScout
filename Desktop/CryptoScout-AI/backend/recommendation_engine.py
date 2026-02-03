
# backend/recommendation_engine.py

from database import get_all_projects


# -------------------------
# User profiles
# -------------------------

PROFILES = {

    "safe": {
        "score": 0.3,
        "confidence": 0.5,
        "volatility": -0.2
    },

    "balanced": {
        "score": 0.4,
        "confidence": 0.3,
        "volatility": -0.1,
        "growth": 0.2
    },

    "aggressive": {
        "score": 0.4,
        "growth": 0.4,
        "volatility": -0.2
    },

    "short-term": {
        "momentum": 0.5,
        "growth": 0.3,
        "risk": -0.2
    },

    "long-term": {
        "score": 0.5,
        "confidence": 0.3,
        "stability": 0.2
    }
}


# -------------------------
# Feature extraction
# -------------------------

def extract_features(project):

    return {

        "score": project.get("score", 0),

        "confidence": project.get("confidence", 0),

        "growth": project.get("price_change_7d", 0),

        "momentum": project.get("price_change_24h", 0),

        "volatility": abs(project.get("price_change_24h", 0)),

        "stability": project.get("market_cap", 0) / 1e9,

        "risk": 1 - project.get("confidence", 0)
    }


# -------------------------
# Core recommender
# -------------------------

def recommend(profile="balanced", top_n=5):

    projects = get_all_projects()

    if profile not in PROFILES:
        profile = "balanced"

    weights = PROFILES[profile]

    scored = []

    for p in projects:

        features = extract_features(p)

        final_score = 0

        for key, weight in weights.items():

            value = features.get(key, 0)

            final_score += value * weight


        scored.append({
            "name": p["name"],
            "symbol": p["symbol"],
            "final_score": round(final_score, 3),
            "base_score": p["score"],
            "confidence": p["confidence"],
            "reasons": p["reasons"]
        })


    scored.sort(key=lambda x: x["final_score"], reverse=True)

    return scored[:top_n]
