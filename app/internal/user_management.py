from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import Form, HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import jwt
from passlib.context import CryptContext
from pydantic import UUID4

from ..config import settings
from .constants import ACCESS_TOKEN_EXPIRE_MINUTES, CREDENTIALS_EXCEPTION, DECODE_ALGORITHM
from .models import TokenPayload
from .user_db_client import UserDBClient, UserModel


def create_access_token(user_id: UUID4):
    token_data = TokenPayload(
        sub=user_id.hex,
        expires=datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    encoded_jwt = jwt.encode(
        token_data.model_dump(mode="json"),
        settings.AUTH_SECRET,
        algorithm=DECODE_ALGORITHM,
    )
    return encoded_jwt


# <------------- GOOGLE ------------->


def verify_google_oauth2_token(oauth2_token: Annotated[str, Form()]):
    try:
        return id_token.verify_oauth2_token(
            oauth2_token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )
    except ValueError:
        raise CREDENTIALS_EXCEPTION


def authenticate_google_user(google_user_id: str, db_client: UserDBClient):
    if user := db_client.get_google_user(google_user_id):
        return user

    raise CREDENTIALS_EXCEPTION


def create_google_user(
    google_user_id: str,
    email: str,
    db_client: UserDBClient,
):
    if existing_user := db_client.get_google_user(google_user_id):
        return existing_user

    new_user = UserModel(id=uuid4(), email=email, google_id=google_user_id, is_disabled=False)
    db_client.save_user(new_user)
    return new_user


# <------------- EMAIL & PASSWORD ------------->

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def authenticate_password_user(email: str, password: str, db_client: UserDBClient):
    user = db_client.get_user_for_email(email=email)

    if not user:
        raise CREDENTIALS_EXCEPTION

    if not pwd_context.verify(password, user.password):
        raise CREDENTIALS_EXCEPTION

    return user


def create_password_user(
    email: str,
    password: str,
    db_client: UserDBClient,
):
    # Note: To mitigate potential sniffing and enumeration attacks, you can consider implementing
    # some best practices, including using generic error messages (avoiding direct indication that
    # an email is already in use), implementing rate limiting, and utilizing CAPTCHA to deter
    # automated scripts.
    if db_client.get_user_for_email(email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    new_user = UserModel(
        id=uuid4(), email=email, password=pwd_context.hash(password), is_disabled=False
    )
    db_client.save_user(new_user)
    return new_user
