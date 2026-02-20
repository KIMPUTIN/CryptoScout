
# backend/services/market_service.py

import requests
import logging
import time
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from core.circuit_breaker import CircuitBreaker
from core.api_usage import APIUsageTracker


logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_SINGLE_URL = "https://api.coingecko.com/api/v3/coins/{id}"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 2

# Create a session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=RETRY_DELAY,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=120
)

api_tracker = APIUsageTracker(window_seconds=3600)


def validate_coin_data(coin: Dict[str, Any]) -> bool:
    """
    Validate that a coin has all required fields with valid data.
    """
    required_fields = ["symbol", "current_price", "name"]
    
    # Check if all required fields exist and have valid values
    for field in required_fields:
        if field not in coin or coin.get(field) is None:
            return False
    
    # Additional validation for numeric fields
    numeric_fields = ["current_price", "market_cap", "total_volume"]
    for field in numeric_fields:
        value = coin.get(field)
        if value is not None and not isinstance(value, (int, float)):
            return False
    
    return True


def extract_price_change_7d(coin: Dict[str, Any]) -> float:
    """
    Safely extract 7-day price change from different possible response formats.
    """
    # Try different possible field names for 7-day price change
    possible_fields = [
        "price_change_percentage_7d_in_currency",
        "price_change_percentage_7d",
        "price_change_7d"
    ]
    
    for field in possible_fields:
        value = coin.get(field)
        if value is not None and isinstance(value, (int, float)):
            return value
    
    return 0.0


def fetch_top_projects(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch top crypto projects from CoinGecko.
    Production-safe with retry + validation.
    
    Args:
        limit: Number of projects to fetch (max 250 for CoinGecko free tier)
    
    Returns:
        List of validated project dictionaries
    """
    # Validate limit
    if limit <= 0 or limit > 250:
        logger.warning(f"Invalid limit {limit}, adjusting to 50")
        limit = 50
    
    # Track API usage
    api_tracker.record_call()

    # Check circuit breaker
    if not breaker.can_execute():
        logger.warning("Circuit breaker OPEN — skipping market request")
        return []

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "7d",
        "locale": "en"  # Add locale for consistent responses
    }

    try:
        # Use session with retry strategy instead of manual retries
        response = session.get(
            COINGECKO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        # Handle rate limiting
        if response.status_code == 429:
            api_tracker.record_rate_limit()
            breaker.record_failure()
            retry_after = response.headers.get('Retry-After', '60')
            logger.warning(f"Rate limited by CoinGecko (429). Retry after {retry_after} seconds")
            return []

        # Handle other HTTP errors
        response.raise_for_status()
        
        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            breaker.record_failure()
            return []

        # Validate response type
        if not isinstance(data, list):
            logger.error(f"Unexpected response type: {type(data)}")
            breaker.record_failure()
            return []

        projects = []
        validation_errors = 0

        for coin in data:
            # Validate coin data
            if not validate_coin_data(coin):
                validation_errors += 1
                logger.debug(f"Skipping invalid coin data: {coin.get('symbol', 'unknown')}")
                continue

            try:
                # Extract 7-day price change safely
                price_change_7d = extract_price_change_7d(coin)
                
                # Create project entry with safe defaults
                project = {
                    "name": str(coin.get("name", "")).strip(),
                    "symbol": str(coin.get("symbol", "")).upper().strip(),
                    "current_price": float(coin.get("current_price", 0) or 0),
                    "market_cap": float(coin.get("market_cap", 0) or 0),
                    "volume_24h": float(coin.get("total_volume", 0) or 0),
                    "price_change_24h": float(coin.get("price_change_percentage_24h", 0) or 0),
                    "price_change_7d": float(price_change_7d),
                    "market_cap_rank": int(coin.get("market_cap_rank", 0) or 0),
                    "image": coin.get("image", ""),  # Optional but useful
                    "last_updated": coin.get("last_updated", "")
                }
                
                # Only include projects with valid symbol
                if project["symbol"] and project["symbol"] != "NULL":
                    projects.append(project)
                else:
                    validation_errors += 1
                    
            except (ValueError, TypeError) as e:
                validation_errors += 1
                logger.debug(f"Data conversion error for {coin.get('symbol', 'unknown')}: {e}")
                continue

        # Log summary
        if validation_errors > 0:
            logger.info(f"Skipped {validation_errors} invalid/malformed entries")
        
        logger.info(f"Successfully fetched {len(projects)} projects from CoinGecko")
        
        # Record success and reset circuit breaker
        breaker.record_success()
        return projects

    except requests.exceptions.Timeout:
        api_tracker.record_failure()
        breaker.record_failure()
        logger.error(f"Request timeout after {REQUEST_TIMEOUT} seconds")
        return []
        
    except requests.exceptions.ConnectionError as e:
        api_tracker.record_failure()
        breaker.record_failure()
        logger.error(f"Connection error: {e}")
        return []
        
    except requests.exceptions.HTTPError as e:
        api_tracker.record_failure()
        breaker.record_failure()
        logger.error(f"HTTP error: {e}")
        return []
        
    except Exception as e:
        api_tracker.record_failure()
        breaker.record_failure()
        logger.error(f"Unexpected error fetching market data: {e}", exc_info=True)
        return []


def fetch_project_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single project by symbol.
    Note: CoinGecko doesn't support direct symbol lookup, so we need to search.
    This is a helper function for single project scans.
    
    Args:
        symbol: Project symbol (e.g., 'BTC')
    
    Returns:
        Single project dictionary or None if not found
    """
    if not symbol:
        return None
    
    # Normalize symbol
    symbol = symbol.upper().strip()
    
    # Fetch top projects and find the one with matching symbol
    # This is more efficient than calling the API for each symbol
    projects = fetch_top_projects(limit=250)  # Get more to increase chance of finding
    
    for project in projects:
        if project.get("symbol") == symbol:
            logger.info(f"Found project {symbol}: {project.get('name')}")
            return project
    
    logger.warning(f"Project with symbol {symbol} not found")
    return None


def fetch_project_by_id(coin_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single project by CoinGecko ID (more precise than symbol).
    
    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin')
    
    Returns:
        Single project dictionary or None if not found
    """
    if not coin_id:
        return None
    
    if not breaker.can_execute():
        logger.warning("Circuit breaker OPEN — skipping single project request")
        return None
    
    url = COINGECKO_SINGLE_URL.format(id=coin_id)
    
    params = {
        "localization": False,
        "tickers": False,
        "market_data": True,
        "community_data": False,
        "developer_data": False,
        "sparkline": False
    }
    
    try:
        response = session.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 429:
            breaker.record_failure()
            logger.warning("Rate limited by CoinGecko (429)")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        # Transform to match the format from fetch_top_projects
        project = {
            "name": data.get("name", ""),
            "symbol": data.get("symbol", "").upper(),
            "current_price": data.get("market_data", {}).get("current_price", {}).get("usd", 0),
            "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd", 0),
            "volume_24h": data.get("market_data", {}).get("total_volume", {}).get("usd", 0),
            "price_change_24h": data.get("market_data", {}).get("price_change_percentage_24h", 0),
            "price_change_7d": data.get("market_data", {}).get("price_change_percentage_7d", 0),
            "market_cap_rank": data.get("market_cap_rank", 0),
            "image": data.get("image", {}).get("large", ""),
            "last_updated": data.get("last_updated", "")
        }
        
        breaker.record_success()
        return project
        
    except Exception as e:
        breaker.record_failure()
        logger.error(f"Failed to fetch project by id {coin_id}: {e}")
        return None


def get_api_usage_stats() -> Dict[str, Any]:
    """
    Get API usage statistics.
    """
    return {
        "calls_last_hour": api_tracker.get_call_count(),
        "rate_limited": api_tracker.get_rate_limit_count(),
        "failures": api_tracker.get_failure_count(),
        "circuit_breaker_state": "OPEN" if breaker.is_open() else "CLOSED"
    }


def clear_api_tracker():
    """
    Clear API usage tracker (useful for testing).
    """
    api_tracker.clear()
    logger.info("API usage tracker cleared")