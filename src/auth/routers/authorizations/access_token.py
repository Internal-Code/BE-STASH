from datetime import timedelta
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseToken
from fastapi import APIRouter, HTTPException, status, Depends
from src.secret import ACCESS_TOKEN_EXPIRED, REFRESH_TOKEN_EXPIRED
from src.auth.utils.jwt.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
)
from src.auth.utils.database.general import update_latest_login, save_tokens

router = APIRouter(tags=["authorizations"], prefix="/auth")


async def access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> ResponseToken:
    credentials_error = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User could not be validated.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        response = ResponseToken()
        user_in_db = await authenticate_user(form_data.username, form_data.password)

        if user_in_db is None:
            raise credentials_error

        latest_login = await update_latest_login(
            username=user_in_db.username, email=user_in_db.email
        )

        if latest_login is True:
            access_token = await create_access_token(
                data={
                    "sub": user_in_db.username,
                    "user_uuid": str(user_in_db.user_uuid),
                },
                access_token_expires=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED)),
            )

            refresh_token = await create_refresh_token(
                data={
                    "sub": user_in_db.username,
                    "user_uuid": str(user_in_db.user_uuid),
                },
                refresh_token_expires=timedelta(minutes=int(REFRESH_TOKEN_EXPIRED)),
            )
        await save_tokens(
            user_uuid=user_in_db.user_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        response.refresh_token = refresh_token
        response.access_token = access_token
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error while generate access_token: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/token",
    response_model=ResponseToken,
    endpoint=access_token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate users and return access token.",
)
