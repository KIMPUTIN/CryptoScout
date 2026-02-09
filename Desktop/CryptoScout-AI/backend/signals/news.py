

# backend/signals/news.py

import os
import requests
import logging
from collections import defaultdict
from textblob import TextBlob
from signals.cache import get, set



logger = logging.getLogger("NEWS_SIGNAL")

GNEWS_KEY = os.getenv("GNEWS_API_KEY")

BASE_URL = "https://gnews.io/api/v4/search"


def fetch_news_impact(symbols, limit=10):

    cache_key = "news_impact"

    cached = get(cache_key)

    if cached:
        return cached

    """
    Returns:
    {
      "BTC": {"score": 0.21, "mentions": 6},
      ...
    }
    """

    if not GNEWS_KEY:
        logger.warning("Missing GNEWS_API_KEY")
        return {}


    results = defaultdict(lambda: {
        "score": 0,
        "mentions": 0
    })


    for sym in symbols:

        try:

            params = {
                "q": sym,
                "token": GNEWS_KEY,
                "lang": "en",
                "max": limit,
                "sortby": "publishedAt"
            }

            r = requests.get(
                BASE_URL,
                params=params,
                timeout=20
            )

            r.raise_for_status()

            data = r.json().get("articles", [])


            for art in data:

                text = f"{art.get('title','')} {art.get('description','')}"

                sentiment = TextBlob(text).sentiment.polarity

                results[sym]["score"] += sentiment
                results[sym]["mentions"] += 1


        except Exception as e:

            logger.warning("GNews error %s: %s", sym, e)


    # Normalize
    for sym in results:

        m = results[sym]["mentions"]

        if m > 0:
            results[sym]["score"] /= m


    set(cache_key, results)


    return results
