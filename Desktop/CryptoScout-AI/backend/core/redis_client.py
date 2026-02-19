
import redis
import os
import json

REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None


def cache_set(key, value, ttl=300):
    if redis_client:
        redis_client.setex(key, ttl, json.dumps(value))


def cache_get(key):
    if redis_client:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    return None
