from uuid import UUID
from src.secret import Config
from datetime import timedelta
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.query import QueryDatabase
from src.schema.response import ResponseToken
from fastapi import APIRouter, status, Depends
from services.postgre.model import UserToken
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from src.schema.request_format import UserLoginPayload
from utils.error import (
    ServiceError,
    StashBaseApiError,
    NotFoundError,
)

config = Config()
jwt_handler = JWTHandler()
router = APIRouter(tags=["User General"], prefix="/user/general")


async def login_endpoint(
    schema: UserLoginPayload,
    unique_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseToken:
    logging.info("Login endpoint.")
    response = ResponseToken()
    query = QueryDatabase(db)
    unique_id = str(unique_id)
    account_record = await jwt_handler.authenticate_user(
        unique_id=unique_id, pin=schema.pin
    )

    try:
        if not account_record:
            logging.error("User not found.")
            raise NotFoundError(detail="User not found.")

        logging.info("Generating access token.")
        access_token = jwt_handler.create_access_token(
            data={"sub": account_record.unique_id},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )

        logging.info("Generating refresh token.")
        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": account_record.unique_id},
            refresh_token_expires=timedelta(days=int(config.REFRESH_TOKEN_EXPIRED)),
        )

        await query.insert(
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
    path="/login/{unique_id}",
    response_model=ResponseToken,
    endpoint=login_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Authenticate users and return access token.",
)
