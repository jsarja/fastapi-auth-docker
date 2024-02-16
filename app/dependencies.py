from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from .config import settings
from .internal.constants import CREDENTIALS_EXCEPTION, DECODE_ALGORITHM
from .internal.models import TokenPayload
from .internal.note_db_client import NoteDBClient, NoteMongoDBClient
from .internal.user_db_client import UserDBClient, UserMongoDBClient


def get_user_db_client() -> UserDBClient:
    return UserMongoDBClient()


def get_note_db_client() -> NoteDBClient:
    return NoteMongoDBClient()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)],
):
    # Check if the token can be converted correctly.
    try:
        payload_dict = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=[DECODE_ALGORITHM],
        )
        token_payload = TokenPayload(**payload_dict)
    except (ValidationError, JWTError):
        raise CREDENTIALS_EXCEPTION

    # Check if the token has expired
    if datetime.now(timezone.utc) > token_payload.expires:
        raise CREDENTIALS_EXCEPTION

    # Check if the token's user exists
    token_user_id = UUID(token_payload.sub)
    user = user_db_client.get_user(user_id=token_user_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION

    return user
