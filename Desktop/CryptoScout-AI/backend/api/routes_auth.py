
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

from database.repository import get_or_create_user

router = APIRouter(prefix="/auth", tags=["Auth"])


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

        access_token = jwt.encode(
            {
                "user_id": user["id"],
                "exp": datetime.utcnow() + timedelta(minutes=15)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        refresh_token = jwt.encode(
            {
                "user_id": user["id"],
                "exp": datetime.utcnow() + timedelta(days=7)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )


@router.post("/refresh")
def refresh(payload: dict):

    token = payload.get("refresh_token")

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        new_access_token = jwt.encode(
            {
                "user_id": decoded["user_id"],
                "exp": datetime.utcnow() + timedelta(minutes=15)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        return {"access_token": new_access_token}

    except:
        raise HTTPException(status_code=401, detail="Invalid refresh token")



        #return {"token": jwt_token, "user": user}  ---------

    #except Exception:  -----------------
        #raise HTTPException(status_code=401, detail="Invalid Google token")--
