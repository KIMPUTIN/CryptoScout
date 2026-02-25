

from datetime import datetime
from fastapi import Depends, Header, HTTPException
import jwt

from core.config import JWT_SECRET, JWT_ALGORITHM
from database.repository import get_user_by_id

#from fastapi.security import OAuth2PasswordBearer ????
#from api.dependencies import get_current_user -------Delete 
#from your_auth_file import get_current_user  # adjust import ----Delete



def get_current_user(authorization: str = Header(None)):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = get_user_by_id(payload["user_id"])

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_pro(current_user = Depends(get_current_user)):

    # No subscription at all
    if not current_user.subscription_expires_at:
        raise HTTPException(
            status_code=403,
            detail="Trader Mode required"
        )

    # Expired subscription
    if current_user.subscription_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail="Subscription expired"
        )

    return current_user



#NOTE: Dependencies must not import routes.
# ------ Correct direction:
#        routes_* → dependencies
#        dependencies → nothing from routes

#        Never reverse it.