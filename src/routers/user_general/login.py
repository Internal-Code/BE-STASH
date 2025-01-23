from src.secret import Config
from datetime import timedelta
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseToken
from src.schema.request_format import UserLogin
from utils.query import insert_record
from services.postgres.models import UserToken
from utils.jwt import JWTHandler
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
)

config = Config()
jwt_handler = JWTHandler(config)
router = APIRouter(tags=["User General"], prefix="/user/general")


async def login_endpoint(
    schema: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> ResponseToken:
    response = ResponseToken()
    account_record = await jwt_handler.authenticate_user(
        unique_id=schema.unique_id, pin=schema.pin
    )

    try:
        if not account_record:
            raise DataNotFoundError(detail="User not found.")

        access_token = jwt_handler.create_access_token(
            data={"sub": account_record.unique_id},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )

        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": account_record.unique_id},
            refresh_token_expires=timedelta(minutes=int(config.REFRESH_TOKEN_EXPIRED)),
        )

        await insert_record(
            db=db,
            table=UserToken,
            data={
                "unique_id": account_record.unique_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
        )

        response.access_token = access_token
        response.refresh_token = refresh_token

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/login",
    response_model=ResponseToken,
    endpoint=login_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Authenticate users and return access token.",
)
