
# backend/scoring.py

import math


# --------------------------------------------------
# NORMALIZATION HELPERS
# --------------------------------------------------

def _safe_log(x):
    return math.log10(x + 1)


def _clamp(v, lo=0, hi=1):
    return max(lo, min(hi, v))


# --------------------------------------------------
# CORE ENGINE
# --------------------------------------------------

def calculate_score(project: dict) -> dict:
    """
    Advanced crypto scoring engine (0–100)
    Includes risk + stability + quality
    """

    # Raw data
    mc = project.get("market_cap", 0)
    vol = project.get("volume_24h", 0)
    d1 = project.get("price_change_24h", 0)
    d7 = project.get("price_change_7d", 0)
    holders = project.get("holders", 0)


    # -------------------------------
    # FUNDAMENTAL STRENGTH (0–1)
    # -------------------------------

    mc_s = _safe_log(mc) / 12
    vol_s = _safe_log(vol) / 12
    hold_s = _safe_log(holders) / 6

    fundamental = _clamp(
        (mc_s * 0.4) + (vol_s * 0.4) + (hold_s * 0.2)
    )


    # -------------------------------
    # MOMENTUM (0–1)
    # -------------------------------

    momentum_raw = (d1 * 0.6) + (d7 * 0.4)

    momentum = _clamp((momentum_raw + 50) / 100)


    # -------------------------------
    # VOLATILITY / RISK (0–1)
    # -------------------------------

    volatility = abs(d1) / 30
    volatility = _clamp(volatility)

    drawdown = max(0, -d7) / 50
    drawdown = _clamp(drawdown)

    risk = _clamp((volatility * 0.6) + (drawdown * 0.4))


    # -------------------------------
    # STABILITY (0–1)
    # -------------------------------

    stability = _clamp(
        (fundamental * 0.6) +
        ((1 - risk) * 0.4)
    )


    # -------------------------------
    # QUALITY (0–1)
    # -------------------------------

    quality = _clamp(
        (fundamental * 0.5) +
        (stability * 0.3) +
        (momentum * 0.2)
    )


    # -------------------------------
    # FINAL SCORE (0–100)
    # -------------------------------

    final = (
        fundamental * 0.35 +
        momentum * 0.25 +
        stability * 0.2 +
        quality * 0.2
    ) * 100


    final_score = round(_clamp(final / 100) * 100, 2)


    # -------------------------------
    # REASONS
    # -------------------------------

    reasons = []

    if fundamental > 0.7:
        reasons.append("Strong fundamentals")

    if momentum > 0.65:
        reasons.append("Positive momentum")

    if risk < 0.3:
        reasons.append("Low volatility risk")

    if stability > 0.7:
        reasons.append("High stability")

    if drawdown > 0.5:
        reasons.append("Recent drawdown risk")

    if not reasons:
        reasons.append("Balanced risk profile")


    return {
        "score": final_score,
        "fundamental": round(fundamental, 3),
        "momentum": round(momentum, 3),
        "risk": round(risk, 3),
        "stability": round(stability, 3),
        "quality": round(quality, 3),
        "reasons": ", ".join(reasons)
    }
