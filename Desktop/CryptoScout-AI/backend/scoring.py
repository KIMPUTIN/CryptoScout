
import math


def calculate_score(project):
    """
    Calculate crypto score (0–100)
    """

    market_cap = project.get("market_cap", 0)
    volume = project.get("volume_24h", 0)
    price_change = project.get("price_change_24h", 0)
    holders = project.get("holders", 0)

    # Normalize safely
    market_score = min(math.log10(market_cap + 1) * 10, 25)
    volume_score = min(math.log10(volume + 1) * 10, 25)

    growth_score = min(abs(price_change) * 2, 25)

    community_score = min(math.log10(holders + 1) * 10, 15)

    risk_score = 10 if price_change > -30 else 0

    total = (
        market_score +
        volume_score +
        growth_score +
        community_score +
        risk_score
    )

    return round(min(total, 100), 2)
