
import requests
from database import save_project
from ai_engine import analyze_project


TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"


def scan_coingecko():
    print("🔍 [SCAN] Starting CoinGecko AI scan")

    try:
        # -------------------------
        # 1. Get trending coins
        # -------------------------
        res = requests.get(TRENDING_URL, timeout=15)
        res.raise_for_status()

        data = res.json()
        coins = data.get("coins", [])

        if not coins:
            print("⚠️ No trending coins found")
            return

        ids = []

        for item in coins:
            ids.append(item["item"]["id"])

        print(f"🔍 [SCAN] Found {len(ids)} coins")

        # -------------------------
        # 2. Get market data
        # -------------------------
        params = {
            "vs_currency": "usd",
            "ids": ",".join(ids),
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d"
        }

        market_res = requests.get(
            MARKETS_URL,
            params=params,
            timeout=20
        )

        market_res.raise_for_status()

        markets = market_res.json()

        if not markets:
            print("⚠️ No market data returned")
            return

        # -------------------------
        # 3. Run AI analysis
        # -------------------------
        for coin in markets:

def safe_number(value, default=0):
    if value is None:
        return default
    try:
        return float(value)
    except:
        return default


        project_data = {
            "name": coin["name"],
            "symbol": coin["symbol"].upper(),

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


            ai_result = analyze_project(project_data)

            project_data.update(ai_result)

            print("💾 [SAVE]", project_data["name"], project_data["score"])

            save_project(project_data)

        print("✅ [SCAN] AI Scan Completed")

    except requests.exceptions.HTTPError as e:
        print("❌ CoinGecko HTTP Error:", e)

    except Exception as e:
        print("❌ Scan Error:", e)
