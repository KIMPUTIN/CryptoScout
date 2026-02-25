

from pydantic import BaseModel


class AIRequest(BaseModel):
    symbol: str