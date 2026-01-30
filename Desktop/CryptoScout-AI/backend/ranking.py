
from database import get_all_projects


def get_short_term():
    projects = get_all_projects()

    return sorted(
        projects,
        key=lambda x: (
            x.get("price_change_24h", 0),
            x.get("volume_24h", 0)
        ),
        reverse=True
    )[:10]


def get_long_term():
    projects = get_all_projects()

    return sorted(
        projects,
        key=lambda x: (
            x.get("score", 0),
            x.get("confidence", 0)
        ),
        reverse=True
    )[:10]


def get_low_risk():
    projects = get_all_projects()

    return sorted(
        projects,
        key=lambda x: (
            x.get("market_cap", 0),
            -abs(x.get("price_change_24h", 0))
        ),
        reverse=True
    )[:10]


def get_high_growth():
    projects = get_all_projects()

    return sorted(
        projects,
        key=lambda x: (
            x.get("score", 0),
            -x.get("market_cap", 0)
        ),
        reverse=True
    )[:10]
