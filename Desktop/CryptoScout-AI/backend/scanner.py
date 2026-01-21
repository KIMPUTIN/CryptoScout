
import requests
from database import save_project
from scoring import analyze_project

COINGECKO_NEW_COINS = "https://api.coingecko.com/api/v3/search/trending"


def scan_coingecko():
    try:
        print("🔍 Scanning CoinGecko for trending crypto...")
        res = requests.get(COINGECKO_NEW_COINS, timeout=15)
        res.raise_for_status()
        data = res.json()

        coins = data.get("coins", [])

        for item in coins:
            try:
                coin = item["item"]

                project = {
                    "name": coin["name"],
                    "symbol": coin["symbol"]
                }

                analysis = analyze_project(project)

                project.update(analysis)
                project["reasons"] = "Trending on CoinGecko. " + project["reasons"]

                save_project(project)
            except Exception as e:
                print(f"⚠️ Error processing coin {item.get('item', {}).get('name', 'unknown')}: {e}")
                continue

        print("✅ Scan completed")
    except Exception as e:
        print(f"❌ Error scanning CoinGecko: {e}")
