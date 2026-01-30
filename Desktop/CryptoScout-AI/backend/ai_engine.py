
import math


def safe(value, default=0):
    if value is None:
        return default
    try:
        return float(value)
    except:
        return default


def analyze_project(data: dict):
    """
    AI-style analysis engine
    Returns: score, verdict, confidence, reasons
    """

    market_cap = safe(data.get("market_cap"))
    volume = safe(data.get("volume_24h"))
    change_24h = safe(data.get("price_change_24h"))
    change_7d = safe(data.get("price_change_7d"))
    rank = safe(data.get("market_cap_rank"))

    # --- Normalize ---
    market_score = min(math.log10(market_cap + 1) * 12, 100)
    volume_score = min(math.log10(volume + 1) * 12, 100)

    momentum_score = min(abs(change_24h) * 2, 50) + min(abs(change_7d) * 1.5, 50)

    stability_score = max(0, 100 - abs(change_24h * 2))

    dominance_score = max(0, 100 - rank / 5)

    # --- Weighted Total ---
    final_score = (
        market_score * 0.20 +
        volume_score * 0.25 +
        momentum_score * 0.25 +
        stability_score * 0.15 +
        dominance_score * 0.15
    )

    final_score = round(min(final_score, 100), 2)

    # --- Verdict ---
    if final_score >= 75:
        verdict = "STRONG BUY 🚀"
    elif final_score >= 60:
        verdict = "BUY ✅"
    elif final_score >= 45:
        verdict = "HOLD ⚠️"
    else:
        verdict = "AVOID ❌"

    # --- Confidence ---
    confidence = round(min(final_score / 100, 1), 2)

    # --- Reasons ---
    reasons = []

    if volume_score > 60:
        reasons.append("High trading volume")

    if momentum_score > 60:
        reasons.append("Strong upward momentum")

    if stability_score > 60:
        reasons.append("Price stability")

    if dominance_score > 60:
        reasons.append("Strong market position")

    if not reasons:
        reasons.append("Weak market signals")

    return {
        "score": final_score,
        "verdict": verdict,
        "confidence": confidence,
        "reasons": ". ".join(reasons)
    }
