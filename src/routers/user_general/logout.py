from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.time_utils import local_time
from utils.query import QueryDatabase
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from src.schema.response import ResponseDefault
from services.postgre.model import BlacklistToken, UserToken
from utils.error import (
    ServiceError,
    StashBaseApiError,
    InvalidTokenError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["User General"], prefix="/user/general")


async def logout_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Logout endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    current_time = local_time()

    try:
        user_token_record = await query.find(
            table=UserToken, unique_id=current_user.unique_id, order_by="desc"
        )
        blacklist_access_token = await query.find(
            table=BlacklistToken,
            access_token=user_token_record.access_token,
            order_by="desc",
        )
        if blacklist_access_token:
            logging.error("Access token blacklisted.")
            raise InvalidTokenError(detail="Access token already blacklisted.")

        blacklist_refresh_token = await query.find(
            table=BlacklistToken,
            refresh_token=user_token_record.refresh_token,
            order_by="desc",
        )
        if blacklist_refresh_token:
            logging.error("Refresh token blacklisted.")
            raise InvalidTokenError(detail="Refresh token already blacklisted.")

        if not (blacklist_refresh_token and blacklist_access_token):
            logging.info("Inserting access token and refresh token into database.")
            await query.insert(
                table=BlacklistToken,
                data={
                    "blacklisted_at": current_time,
                    "unique_id": current_user.unique_id,
                    "access_token": user_token_record.access_token,
                    "refresh_token": user_token_record.refresh_token,
                },
            )

        response.message = "User successfully logged out."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["POST"],
    path="/logout",
    response_model=ResponseDefault,
    endpoint=logout_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Logout logged in current user.",
)
