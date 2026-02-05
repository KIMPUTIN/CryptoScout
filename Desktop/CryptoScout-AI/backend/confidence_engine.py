
# backend/confidence_engine.py


def calculate_confidence(project: dict, score_data: dict) -> float:
    """
    Calibrate confidence (0–1)
    Based on data quality + stability + risk + AI reliability
    """

    # -----------------------------
    # DATA COMPLETENESS
    # -----------------------------

    required = [
        "market_cap",
        "volume_24h",
        "price_change_24h",
        "price_change_7d"
    ]

    present = sum(1 for k in required if project.get(k) is not None)

    data_quality = present / len(required)


    # -----------------------------
    # STABILITY
    # -----------------------------

    stability = score_data.get("stability", 0.5)


    # -----------------------------
    # RISK (INVERT)
    # -----------------------------

    risk = score_data.get("risk", 0.5)

    risk_score = 1 - risk


    # -----------------------------
    # AI RELIABILITY
    # -----------------------------

    ai_conf = project.get("confidence", 0.5)


    # -----------------------------
    # FINAL CONFIDENCE
    # -----------------------------

    confidence = (
        data_quality * 0.25 +
        stability * 0.25 +
        risk_score * 0.25 +
        ai_conf * 0.25
    )

    return round(max(0, min(1, confidence)), 3)
