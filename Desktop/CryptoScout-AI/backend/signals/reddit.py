
# backend/signals/reddit.py

import os
import requests
import logging
from collections import defaultdict
from textblob import TextBlob


logger = logging.getLogger("REDDIT_SIGNAL")

RAPID_KEY = os.getenv("RAPIDAPI_KEY")

RAPID_HOST = "reddit-scraper2.p.rapidapi.com"


BASE_URL = "https://reddit-scraper2.p.rapidapi.com/search"


def fetch_sentiment(symbols, limit=50):

    if not RAPID_KEY:
        logger.warning("Missing RAPIDAPI_KEY")
        return {}


    results = defaultdict(lambda: {
        "score": 0,
        "mentions": 0
    })


    headers = {
        "X-RapidAPI-Key": RAPID_KEY,
        "X-RapidAPI-Host": RAPID_HOST
    }


    for sym in symbols:

        try:

            params = {
                "q": sym,
                "sort": "new",
                "limit": limit
            }

            r = requests.get(
                BASE_URL,
                headers=headers,
                params=params,
                timeout=20
            )

            r.raise_for_status()

            data = r.json().get("data", [])


            for post in data:

                text = f"{post.get('title','')} {post.get('text','')}"

                sentiment = TextBlob(text).sentiment.polarity

                results[sym]["score"] += sentiment
                results[sym]["mentions"] += 1


        except Exception as e:

            logger.warning("RapidAPI error %s: %s", sym, e)


    # Normalize
    for sym in results:

        m = results[sym]["mentions"]

        if m > 0:
            results[sym]["score"] /= m


    return results
