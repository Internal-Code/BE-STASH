from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.auth.schema.response import ResponseToken
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.utils.database.general import save_tokens
from src.secret import ACCESS_TOKEN_EXPIRED, REFRESH_TOKEN_EXPIRED
from src.auth.routers.exceptions import (
    ServiceError,
    FinanceTrackerApiError,
    AuthenticationFailed,
)
from src.auth.utils.jwt.general import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(tags=["authorizations"], prefix="/auth")


async def access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> ResponseToken:
    try:
        response = ResponseToken()
        user_in_db = await authenticate_user(form_data.username, form_data.password)

        if user_in_db is None:
            raise AuthenticationFailed(detail="User could not be validated.")

        access_token = await create_access_token(
            data={"sub": user_in_db.user_uuid},
            access_token_expires=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED)),
        )

        refresh_token = await create_refresh_token(
            data={"sub": user_in_db.user_uuid},
            refresh_token_expires=timedelta(minutes=int(REFRESH_TOKEN_EXPIRED)),
        )
        await save_tokens(
            user_uuid=user_in_db.user_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        response.refresh_token = refresh_token
        response.access_token = access_token

    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["POST"],
    path="/token",
    response_model=ResponseToken,
    endpoint=access_token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate users and return access token.",
)
