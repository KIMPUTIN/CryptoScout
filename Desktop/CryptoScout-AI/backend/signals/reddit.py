
# backend/signals/reddit.py

import requests
import logging
from collections import defaultdict
from textblob import TextBlob


logger = logging.getLogger("REDDIT_SIGNAL")

PUSHSHIFT_URL = "https://api.pushshift.io/reddit/search/submission/"


def fetch_sentiment(symbols, limit=100):
    """
    Fetch Reddit sentiment using Pushshift (no auth)

    Returns:
    {
      "BTC": {"score": 0.15, "mentions": 42},
      ...
    }
    """

    results = defaultdict(lambda: {
        "score": 0,
        "mentions": 0
    })


    for sym in symbols:

        try:

            params = {
                "q": sym,
                "size": limit,
                "sort": "desc",
                "sort_type": "created_utc"
            }

            r = requests.get(
                PUSHSHIFT_URL,
                params=params,
                timeout=20
            )

            r.raise_for_status()

            data = r.json().get("data", [])


            for post in data:

                text = f"{post.get('title','')} {post.get('selftext','')}"

                sentiment = TextBlob(text).sentiment.polarity

                results[sym]["score"] += sentiment
                results[sym]["mentions"] += 1


        except Exception as e:

            logger.warning("Pushshift error %s: %s", sym, e)


    # Normalize
    for sym in results:

        m = results[sym]["mentions"]

        if m > 0:
            results[sym]["score"] /= m


    return results
