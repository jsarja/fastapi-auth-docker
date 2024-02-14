from functools import wraps

from fastapi import HTTPException, status

from ..config import settings


def google_auth(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_418_IM_A_TEAPOT,
                detail="Google OAuth2 not enabled.",
            )

        return await func(*args, **kwargs)

    return wrapper
