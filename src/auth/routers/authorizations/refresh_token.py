from typing import Annotated
from jose import jwt, JWTError
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.jwt.security import get_current_active_user
from src.auth.schema.response import ResponseToken
from src.auth.utils.database.general import local_time, is_refresh_token_blacklisted
from src.auth.utils.logging import logging
from src.secret import (
    REFRESH_TOKEN_SECRET_KEY,
    ACCESS_TOKEN_SECRET_KEY,
    ACCESS_TOKEN_ALGORITHM,
    ACCESS_TOKEN_EXPIRED,
)

router = APIRouter(tags=["authorizations"], prefix="/auth")


async def refresh_access_token(
    refresh_token: str, current_user: Annotated[dict, Depends(get_current_active_user)]
) -> ResponseToken:
    invalid_refresh_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
    )

    blacklisted_refresh_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token already blacklisted.",
    )

    response = ResponseToken()

    try:
        validate_refresh_token = await is_refresh_token_blacklisted(
            refresh_token=refresh_token
        )

        if validate_refresh_token is True:
            raise blacklisted_refresh_token

        payload = jwt.decode(
            token=refresh_token,
            key=REFRESH_TOKEN_SECRET_KEY,
            algorithms=[ACCESS_TOKEN_ALGORITHM],
        )
        username = payload.get("sub")
        user_uuid = payload.get("user_uuid")
        if user_uuid is None or username is None:
            raise invalid_refresh_token

        access_token_exp = timedelta(minutes=int(ACCESS_TOKEN_EXPIRED))
        new_access_token = jwt.encode(
            {
                "sub": username,
                "user_uuid": user_uuid,
                "exp": local_time() + access_token_exp,
            },
            key=ACCESS_TOKEN_SECRET_KEY,
            algorithm=ACCESS_TOKEN_ALGORITHM,
        )

        response.access_token = new_access_token
        response.token_type = "Bearer"

    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise invalid_refresh_token
    return response


router.add_api_route(
    methods=["POST"],
    path="/refresh-token",
    response_model=ResponseToken,
    endpoint=refresh_access_token,
    status_code=status.HTTP_200_OK,
    summary="Generate new access token.",
)
