
# backend/core/config.py

import os
from datetime import timedelta


# =====================================================
# ENVIRONMENT
# =====================================================

APP_NAME = "CryptoScout API"
ENV = os.getenv("ENV", "development")

# =====================================================
# SECURITY
# =====================================================

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# =====================================================
# DATABASE
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "cryptoscout.db")

# =====================================================
# AI
# =====================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = "gpt-4o-mini"
AI_TIMEOUT = 20
AI_MAX_RETRIES = 2

# =====================================================
# RANKING CACHE
# =====================================================

RANKING_CACHE_DURATION = timedelta(minutes=5)

# =====================================================
# CORS
# =====================================================

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")
