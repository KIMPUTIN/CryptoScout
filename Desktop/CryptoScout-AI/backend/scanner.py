
import requests
from database import save_project
from scoring import analyze_project

COINGECKO_TRENDING = "https://api.coingecko.com/api/v3/search/trending"


def scan_coingecko():
    print("🔍 [SCAN] Starting CoinGecko scan")

    try:
        res = requests.get(COINGECKO_TRENDING, timeout=15)
        print("🔍 [SCAN] Status code:", res.status_code)

        
        data = res.json()
        coins = data.get("coins", [])

        print(f"🔍 [SCAN] Found {len(coins)} coins")

        
        for item in coins:
            coin = item["item"]

            project = {
                "name": coin["name"],
                "symbol": coin["symbol"]
            }

            analysis = analyze_project(project)
            project.update(analysis)
            project["reasons"] = "Trending on CoinGecko. " + project["reasons"]

            print("💾 [SAVE]", project["name"], project["symbol"])
            save_project(project)

        print("✅ [SCAN] Completed")

        
    except Exception as e:
        print(f"❌ Error scanning CoinGecko: {e}")
