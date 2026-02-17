
# backend/scanner.py

import time
import logging
import requests
from datetime import datetime

from database import save_project, get_all_projects
from ai_engine import analyze_project
from scoring import calculate_score
from confidence_engine import calculate_confidence
from signals.reddit import fetch_sentiment
from signals.news import fetch_news_impact


# ==========================================
# CONFIG
# ==========================================

TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

MAX_AI_CALLS = 5
REQUEST_TIMEOUT = 20
RETRY_LIMIT = 3
MAX_SCAN_TIME = 120  # seconds


# ==========================================
# SCAN STATUS (GLOBAL STATE)
# ==========================================

SCAN_STATUS = {
    "last_run": None,
    "last_duration": None,
    "last_result": "UNKNOWN",
    "failure_count": 0
}

FAILURE_COUNT = 0
MAX_FAILURES = 5
COOLDOWN_SECONDS = 600
LAST_FAILURE_TIME = 0


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | SCANNER | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SCANNER")


# ==========================================
# HELPERS
# ==========================================

def safe_number(v, default=0):
    try:
        return float(v)
    except:
        return default


def get_scan_status():
    return {
        "scanner": SCAN_STATUS,
        "api_failures": FAILURE_COUNT
    }


def _fetch(url, params=None):
    """
    Circuit-breaker protected API fetch
    """
    global FAILURE_COUNT, LAST_FAILURE_TIME

    if FAILURE_COUNT >= MAX_FAILURES:
        elapsed = time.time() - LAST_FAILURE_TIME
        if elapsed < COOLDOWN_SECONDS:
            logger.error("Circuit breaker active — skipping API call")
            return None
        else:
            logger.info("Circuit breaker reset")
            FAILURE_COUNT = 0

    for attempt in range(RETRY_LIMIT):
        try:
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            FAILURE_COUNT = 0
            return r.json()
        except Exception as e:
            logger.warning("Fetch retry %s failed: %s", attempt + 1, e)
            time.sleep(2 ** attempt)

    FAILURE_COUNT += 1
    LAST_FAILURE_TIME = time.time()
    logger.error("API failure count: %s", FAILURE_COUNT)
    return None


# ==========================================
# MAIN SCANNER
# ==========================================

def scan_coingecko():

    global SCAN_STATUS

    start_time = time.time()

    try:
        logger.info("Starting CoinGecko scan")

        existing = get_all_projects()

        # ----------------------------------
        # Trending
        # ----------------------------------
        trending = _fetch(TRENDING_URL)

        if not trending:
            raise RuntimeError("Trending API failed")

        coins = trending.get("coins", [])
        if not coins:
            raise RuntimeError("No trending coins found")

        ids = [c["item"]["id"] for c in coins]

        # ----------------------------------
        # Market Data
        # ----------------------------------
        params = {
            "vs_currency": "usd",
            "ids": ",".join(ids),
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d"
        }

        markets = _fetch(MARKETS_URL, params)

        if not markets:
            logger.warning("Using cached DB data")
            if not existing:
                raise RuntimeError("Market API down and no cache available")

            markets = [
                {
                    "name": p["name"],
                    "symbol": p["symbol"],
                    "market_cap": p.get("market_cap"),
                    "total_volume": p.get("volume_24h"),
                    "price_change_percentage_24h": p.get("price_change_24h"),
                    "price_change_percentage_7d_in_currency": p.get("price_change_7d"),
                    "market_cap_rank": 500
                }
                for p in existing
            ]

        symbols = [c.get("symbol", "").upper() for c in markets]

        try:
            sentiment_data = fetch_sentiment(symbols) or {}
        except:
            sentiment_data = {}

        try:
            news_data = fetch_news_impact(symbols) or {}
        except:
            news_data = {}

        ai_calls = 0

        for coin in markets:

            if time.time() - start_time > MAX_SCAN_TIME:
                logger.error("Scan timeout reached")
                break

            symbol = coin.get("symbol", "").upper()

            project = {
                "name": coin.get("name"),
                "symbol": symbol,
                "market_cap": safe_number(coin.get("market_cap")),
                "volume_24h": safe_number(coin.get("total_volume")),
                "price_change_24h": safe_number(
                    coin.get("price_change_percentage_24h")
                ),
                "price_change_7d": safe_number(
                    coin.get("price_change_percentage_7d_in_currency")
                ),
                "market_cap_rank": safe_number(
                    coin.get("market_cap_rank"), 500
                ),
            }

            # AI
            if ai_calls < MAX_AI_CALLS:
                try:
                    project.update(analyze_project(project))
                except:
                    project["confidence"] = 0.3
                    project["verdict"] = "Hold"
                ai_calls += 1

            # Score
            score_data = calculate_score(project)
            project.update(score_data)

            # Confidence
            project["confidence"] = calculate_confidence(project, score_data)

            # Sentiment
            sent = sentiment_data.get(symbol, {})
            project["sentiment_score"] = round(sent.get("score", 0), 3)
            project["social_volume"] = sent.get("mentions", 0)

            # News
            news = news_data.get(symbol, {})
            project["trend_score"] = round(news.get("score", 0), 3)
            project["news_volume"] = news.get("mentions", 0)

            save_project(project)
            time.sleep(0.3)

        duration = round(time.time() - start_time, 2)

        SCAN_STATUS.update({
            "last_run": datetime.utcnow().isoformat(),
            "last_duration": duration,
            "last_result": "HEALTHY",
            "failure_count": 0
        })

        logger.info("Scan completed in %s seconds", duration)

    except Exception as e:

        duration = round(time.time() - start_time, 2)

        logger.error("SCAN FAILED: %s", e)

        SCAN_STATUS.update({
            "last_run": datetime.utcnow().isoformat(),
            "last_duration": duration,
            "last_result": "FAILED",
            "failure_count": SCAN_STATUS["failure_count"] + 1
        })
