from datetime import datetime

from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str  # Subject of the JWT
    expires: datetime
