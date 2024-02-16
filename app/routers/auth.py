from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..dependencies import get_user_db_client
from ..internal.decorators import google_auth
from ..internal.user_db_client import UserDBClient
from ..internal.user_management import (
    authenticate_google_user,
    authenticate_password_user,
    create_access_token,
    create_google_user,
    create_password_user,
    verify_google_oauth2_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token")
async def sign_in(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)],
) -> Token:
    user = authenticate_password_user(
        email=form_data.username, password=form_data.password, db_client=user_db_client
    )
    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register")
async def sign_up(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)],
) -> Token:

    user = create_password_user(
        email=form_data.username, password=form_data.password, db_client=user_db_client
    )

    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/token/google")
@google_auth
async def sign_in_google(
    oauth2_token: Annotated[str, Form()],
    user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)],
) -> Token:
    idinfo = verify_google_oauth2_token(oauth2_token)
    user = authenticate_google_user(
        google_user_id=idinfo["sub"],
        db_client=user_db_client,
    )

    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register/google")
@google_auth
async def sign_up_google(
    oauth2_token: Annotated[str, Form()],
    user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)],
) -> Token:
    idinfo = verify_google_oauth2_token(oauth2_token)

    user = create_google_user(
        google_user_id=idinfo["sub"],
        email=idinfo.get("email", ""),
        db_client=user_db_client,
    )

    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")
