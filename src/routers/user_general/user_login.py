from src.secret import Config
from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseToken
from fastapi.security import OAuth2PasswordRequestForm
from utils.query.general import insert_record
from services.postgres.models import UserToken
from utils.jwt import authenticate_user, create_access_token, create_refresh_token
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
)

config = Config()
router = APIRouter(tags=["User General"], prefix="/user/general")


async def login_endpoint(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(get_db)
) -> ResponseToken:
    response = ResponseToken()
    account_record = await authenticate_user(unique_id=form_data.username, pin=form_data.password)

    try:
        if not account_record:
            raise DataNotFoundError(detail="User not found.")

        access_token = create_access_token(
            data={"sub": account_record.unique_id},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )

        refresh_token = create_refresh_token(
            data={"sub": account_record.unique_id},
            refresh_token_expires=timedelta(minutes=int(config.REFRESH_TOKEN_EXPIRED)),
        )

        await insert_record(
            db=db,
            table=UserToken,
            data={"unique_id": account_record.unique_id, "access_token": access_token, "refresh_token": refresh_token},
        )

        response.access_token = access_token
        response.refresh_token = refresh_token

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["POST"],
    path="/login",
    response_model=ResponseToken,
    endpoint=login_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Authenticate users and return access token.",
)
