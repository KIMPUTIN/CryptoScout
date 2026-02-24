
# backend/payments.py

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException
from coinbase_commerce.client import Client
from your_auth_file import get_current_user   # adjust to your project
from your_database_file import get_user_by_id, update_user_subscription  # adjust

router = APIRouter()

client = Client(api_key=os.getenv("COINBASE_COMMERCE_API_KEY"))


@router.post("/create-crypto-checkout")
async def create_crypto_checkout(current_user=Depends(get_current_user)):

    try:
        charge = client.charge.create(
            name="CryptoScout AI – Trader Mode",
            description="30 days full access to institutional-grade crypto analysis.",
            pricing_type="fixed_price",
            local_price={
                "amount": "12.00",
                "currency": "USD"
            },
            metadata={
                "user_id": str(current_user.id)
            }
        )

        return {"checkout_url": charge.hosted_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coinbase-webhook")
async def coinbase_webhook(request: Request):

    event = await request.json()

    if event["type"] == "charge:confirmed":

        user_id = event["data"]["metadata"]["user_id"]

        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        now = datetime.utcnow()

        # If user already active → extend
        if user.subscription_expires_at and user.subscription_expires_at > now:
            new_expiry = user.subscription_expires_at + timedelta(days=30)
        else:
            new_expiry = now + timedelta(days=30)

        update_user_subscription(
            user_id=user_id,
            subscription_plan="pro",
            subscription_status="active",
            subscription_expires_at=new_expiry
        )

    return {"status": "success"}