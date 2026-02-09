

# backend/signals/cache.py

import time


# In-memory cache (simple MVP)
_cache = {}


CACHE_TTL = 60 * 60   # 1 hour


def get(key):

    data = _cache.get(key)

    if not data:
        return None

    value, ts = data

    if time.time() - ts > CACHE_TTL:
        del _cache[key]
        return None

    return value


def set(key, value):

    _cache[key] = (value, time.time())
