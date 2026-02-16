

# backend/scanner.py

import time
import logging
import requests

from database import save_project, get_all_projects
from ai_engine import analyze_project
from scoring import calculate_score
from confidence_engine import calculate_confidence
from signals.reddit import fetch_sentiment
from signals.news import fetch_news_impact




# --------------------------------------------------
# CONFIG
# --------------------------------------------------

TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

MAX_AI_CALLS = 5          # limit per scan
REQUEST_TIMEOUT = 20
RETRY_LIMIT = 3
# -----------------------------
# Circuit Breaker
# -----------------------------
FAILURE_COUNT = 0
MAX_FAILURES = 5
COOLDOWN_SECONDS = 600  # 10 minutes
LAST_FAILURE_TIME = 0


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    # --format="%(asctime)s [SCANNER] %(levelname)s: %(message)s" --
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SCANNER")


# --------------------------------------------------
# UTILS
# --------------------------------------------------

def safe_number(v, default=0):

    try:
        return float(v)
    except:
        return default

# ----------------------------- Circuit breaker logic ---------------
def _fetch(url, params=None):

    global FAILURE_COUNT, LAST_FAILURE_TIME

    # If in cooldown, skip request
    if FAILURE_COUNT >= MAX_FAILURES:
        elapsed = time.time() - LAST_FAILURE_TIME
        if elapsed < COOLDOWN_SECONDS:
            logger.error("Circuit breaker active — skipping API call")
            return None
        else:
            logger.info("Cooldown expired — resetting circuit breaker")
            FAILURE_COUNT = 0

    for i in range(RETRY_LIMIT):

        try:
            r = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            r.raise_for_status()

            # Success resets failure counter
            FAILURE_COUNT = 0
            return r.json()

        except Exception as e:
            logger.warning("Fetch retry %s: %s", i + 1, e)
            time.sleep(2 ** i)

    # After retries fail
    FAILURE_COUNT += 1
    LAST_FAILURE_TIME = time.time()

    logger.error("API failure count: %s", FAILURE_COUNT)
    return None
# -------------------------------------------------------------------


def _already_scanned(symbol, db_cache):

    return any(p["symbol"] == symbol for p in db_cache)


# --------------------------------------------------
# MAIN SCAN ENGINE
# --------------------------------------------------

def scan_coingecko():

    try:
        start_time = time.time() # ----------------- inserted -----

        logger.info("Starting CoinGecko scan")

        existing = get_all_projects()

        # -----------------------------
        # Trending
        # -----------------------------
        data = _fetch(TRENDING_URL)

        if not data:
            logger.warning("Trending fetch failed — skipping scan")
            return

        coins = data.get("coins", [])

        if not coins:
            logger.warning("No trending coins found")
            return

        ids = [c["item"]["id"] for c in coins]

        logger.info("Found %s trending coins", len(ids))

        # -----------------------------
        # Market Data
        # -----------------------------
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

        # ---New code instead
        if not markets:
            logger.error("Market API down")
            logger.warning("Using cached database data")

            if not existing:
                logger.error("No cached data available")
                return
            
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
        # --------------------


        # -----------------------------
        # Reddit Sentiment
        # -----------------------------
        symbols = [c.get("symbol", "").upper() for c in markets]

        sentiment_data = fetch_sentiment(symbols) or {}
        news_data = fetch_news_impact(symbols) or {}

        # -----------------------------
        # Analysis Pipeline
        # -----------------------------
        ai_calls = 0

        for coin in markets:

            try:

                symbol = coin.get("symbol", "").upper()

                if _already_scanned(symbol, existing):
                    continue

                project = {
                    "name": coin.get("name", "Unknown"),
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

                # -----------------------------
                # AI (Limited)
                # -----------------------------
                if ai_calls < MAX_AI_CALLS:
                    ai = analyze_project(project)
                    project.update(ai)
                    ai_calls += 1
                else:
                    project["confidence"] = 0.4
                    project["verdict"] = "Hold"
                    project["ai_analysis"] = "AI limit reached"
                    project["strategy"] = "Wait"

                # -----------------------------
                # Score
                # -----------------------------
                score_data = calculate_score(project)
                project.update(score_data)

                # -----------------------------
                # Confidence
                # -----------------------------
                project["confidence"] = calculate_confidence(project, score_data)

                # -----------------------------
                # Social Signals
                # -----------------------------
                sent = sentiment_data.get(symbol, {})
                project["sentiment_score"] = round(sent.get("score", 0), 3)
                project["social_volume"] = sent.get("mentions", 0)

                # -----------------------------
                # News Signals
                # -----------------------------
                news = news_data.get(symbol, {})
                project["trend_score"] = round(news.get("score", 0), 3)
                project["news_volume"] = news.get("mentions", 0)

                logger.info(
                    "Saving %s | Score %.2f | Conf %.2f",
                    project["name"],
                    project.get("score", 0),
                    project["confidence"]
                )

                save_project(project)

            # ----inserted with try ---------------------------------
            except Exception as coin_error:
                logger.error("Coin processing failed: %s", coin_error)
                continue
            # -------------------------------------------------------

            time.sleep(0.4)

        duration = round(time.time() - start_time, 2)
        logger.info("Scan completed successfully in %s seconds", duration)
    

        logger.info("Scan completed successfully")
        logger.info("SCAN STATUS: HEALTHY")


    except Exception as e:
        logger.error("SCAN CRASHED: %s", e)
        import traceback
        traceback.print_exc()
        logger.error("SCAN STATUS: FAILED")

