
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


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCANNER] %(levelname)s: %(message)s"
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


def _fetch(url, params=None):

    for i in range(RETRY_LIMIT):

        try:

            r = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            r.raise_for_status()

            return r.json()


        except Exception as e:

            logger.warning("Fetch retry %s: %s", i+1, e)

            time.sleep(2 ** i)


    raise RuntimeError("Fetch failed")


def _already_scanned(symbol, db_cache):

    return any(p["symbol"] == symbol for p in db_cache)


# --------------------------------------------------
# MAIN SCAN ENGINE
# --------------------------------------------------

def scan_coingecko():

    logger.info("Starting CoinGecko scan")


    # -----------------------------
    # Load DB cache
    # -----------------------------

    existing = get_all_projects()


    # -----------------------------
    # Trending
    # -----------------------------

    data = _fetch(TRENDING_URL)

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

    # -----------------------------
    # Reddit Sentiment
    # -----------------------------

    symbols = [c.get("symbol", "").upper() for c in markets]

    sentiment_data = fetch_sentiment(symbols)


    # -----------------------------
    # News Impact
    # -----------------------------

    news_data = fetch_news_impact(symbols)




    if not markets:

        logger.warning("No market data returned")
        return


    # -----------------------------
    # Analysis Pipeline
    # -----------------------------

    ai_calls = 0


    for coin in markets:

        symbol = coin.get("symbol", "").upper()

        if _already_scanned(symbol, existing):
            logger.info("Skipping cached %s", symbol)
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

            logger.info("AI limit reached, fallback used")

            project["confidence"] = 0.4
            project["verdict"] = "HOLD"
            project["ai_analysis"] = "AI budget limit"
            project["strategy"] = "Wait"


        # -----------------------------
        # Scoring
        # -----------------------------

        score_data = calculate_score(project)

        project.update(score_data)


        # -----------------------------
        # Confidence
        # -----------------------------

        conf = calculate_confidence(project, score_data)

        project["confidence"] = conf


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




        # -----------------------------
        # Save
        # -----------------------------

        import time    #Newly included
        time.sleep(0.5)


        logger.info("Saving %s | Score %.2f | Conf %.2f",
                    project["name"],
                    project["score"],
                    project["confidence"])

        save_project(project)


    logger.info("Scan completed")
