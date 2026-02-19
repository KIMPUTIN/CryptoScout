
# backend/services/sentiment_service.py

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def compute_sentiment(project: Dict) -> float:
    """
    Simple rule-based sentiment estimation.
    Returns value between 0 and 1.
    """

    try:
        change_24h = float(project.get("price_change_24h") or 0)
        change_7d = float(project.get("price_change_7d") or 0)

        score = 0

        # Positive momentum bias
        if change_24h > 0:
            score += 0.4
        if change_7d > 0:
            score += 0.4

        # Strong weekly trend bonus
        if change_7d > 10:
            score += 0.2

        return min(score, 1.0)

    except Exception as e:
        logger.warning("Sentiment fallback triggered: %s", e)
        return 0.5
