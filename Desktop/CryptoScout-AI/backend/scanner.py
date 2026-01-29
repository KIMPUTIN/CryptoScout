
import requests
from database import save_project
from scoring import calculate_score

TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"


def get_market_data(ids):
    """Fetch detailed market data for coins (rate-limit safe)"""

    params = {
        "vs_currency": "usd",
        "ids": ",".join(ids),
        "order": "market_cap_desc",
        "per_page": len(ids),
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }

    try:
        res = requests.get(MARKETS_URL, params=params, timeout=15)

        # Handle rate limit
        if res.status_code == 429:
            print("⚠️ CoinGecko rate limit hit. Skipping market data.")
            return []

        res.raise_for_status()
        return res.json()

    except Exception as e:
        print("⚠️ Market data error:", e)
        return []



def scan_coingecko():
    print("🔍 [SCAN] Starting CoinGecko scan")

    try:
        # Step 1: Get trending
        res = requests.get(TRENDING_URL, timeout=15)
        print("🔍 [SCAN] Status code:", res.status_code)

        data = res.json()
        coins = data.get("coins", [])

        print(f"🔍 [SCAN] Found {len(coins)} coins")

        if not coins:
            return

        # Step 2: Extract IDs
        ids = [c["item"]["id"] for c in coins]

        # Step 3: Get market data
        market_data = get_market_data(ids)

        market_map = {}
        if market_data:
            market_map = {c["id"]: c for c in market_data}

        # Step 4: Process coins
        for item in coins:
            coin = item["item"]
            coin_id = coin["id"]

            market = market_map.get(coin_id, {})

            project = {
                "name": coin["name"],
                "symbol": coin["symbol"],

                "market_cap": market.get("market_cap", 0),
                "volume_24h": market.get("total_volume", 0),
                "price_change_24h": market.get("price_change_percentage_24h", 0),
                "holders": market.get("circulating_supply", 0)  # proxy
            }

            print("📊 Data:", project["name"], project["market_cap"], project["volume_24h"])


            analysis = calculate_score(project)
            project.update(analysis)

            project["reasons"] = "Trending on CoinGecko. " + project["reasons"]

            print("💾 [SAVE]", project["name"], project["symbol"])
            save_project(project)

        print("✅ [SCAN] Completed")

    except Exception as e:
        print(f"❌ Error scanning CoinGecko: {e}")

