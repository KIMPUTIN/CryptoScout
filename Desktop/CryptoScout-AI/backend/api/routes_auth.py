
# backend/api/routes_auth.py

import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from core.config import (
    GOOGLE_CLIENT_ID,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRY_DAYS
)

from database.repository import (
    get_or_create_user,
    store_refresh_token,
    is_refresh_token_valid
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# =====================================================
# GOOGLE LOGIN
# =====================================================

@router.post("/google")
async def auth_google(payload: dict):

    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        user = get_or_create_user(
            idinfo["sub"],
            idinfo.get("email"),
            idinfo.get("name"),
            idinfo.get("picture")
        )

        # 🔐 access token (short-lived)
        access_token = jwt.encode(
            {
                "user_id": user["id"],
                "type": "access",
                "exp": datetime.utcnow() + timedelta(minutes=15)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        # 🔐 refresh token (long-lived)
        refresh_token = jwt.encode(
            {
                "user_id": user["id"],
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        # ✅ store refresh token in DB
        store_refresh_token(user["id"], refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")


# =====================================================
# REFRESH ACCESS TOKEN
# =====================================================

@router.post("/refresh")
def refresh(payload: dict):

    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token missing")

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # ✅ check DB validity
        if not is_refresh_token_valid(token):
            raise HTTPException(status_code=401, detail="Token revoked")

        new_access_token = jwt.encode(
            {
                "user_id": decoded["user_id"],
                "type": "access",
                "exp": datetime.utcnow() + timedelta(minutes=15)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        return {"access_token": new_access_token}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
