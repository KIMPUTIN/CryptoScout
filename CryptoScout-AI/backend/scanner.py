


import requests

def scan_projects():
    url = "https://api.coingecko.com/api/v3/search/trending"
    data = requests.get(url).json()

    projects = []
    for item in data.get("coins", []):
        coin = item["item"]
        projects.append({
            "name": coin["name"],
            "symbol": coin["symbol"],
            "website": coin.get("homepage", "")
        })
    return projects