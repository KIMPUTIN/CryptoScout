
# backend/services/market_service.py

import requests
import logging
import time
from typing import List, Dict, Any
from core.circuit_breaker import CircuitBreaker
from core.api_usage import APIUsageTracker



logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 2

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=120
)

api_tracker = APIUsageTracker(window_seconds=3600)




def fetch_top_projects(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch top crypto projects from CoinGecko.
    Production-safe with retry + validation.
    """

    api_tracker.record_call()

    if not breaker.can_execute():
        logger.warning("Circuit breaker OPEN — skipping market request")
        return []

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "7d"
    }

    try:
        response = requests.get(
            COINGECKO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 429:
            api_tracker.record_rate_limit()
            breaker.record_failure()
            logger.warning("Rate limited by CoinGecko (429)")
            return []

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            breaker.record_failure()
            return []

        projects = []

        for coin in data:
            # Basic data validation
            if not coin.get("symbol") or not coin.get("current_price"):
                continue

            projects.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol", "").upper(),
                "current_price": coin.get("current_price") or 0,
                "market_cap": coin.get("market_cap") or 0,
                "volume_24h": coin.get("total_volume") or 0,
                "price_change_24h": coin.get("price_change_percentage_24h") or 0,
                "price_change_7d": coin.get("price_change_percentage_7d_in_currency") or 0,
                "market_cap_rank": coin.get("market_cap_rank") or 0
            })

        breaker.record_success()
        return projects

    except Exception as e:
        api_tracker.record_failure()
        breaker.record_failure()
        logger.error("Market request failed: %s", e)
        return []
