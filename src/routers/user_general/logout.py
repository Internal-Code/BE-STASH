from typing import Annotated
from fastapi import APIRouter, status, Depends
from services.postgres.models import BlacklistToken, UserToken
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseDefault
from utils.jwt import JWTHandler
from src.secret import Config
from utils.helper import local_time
from utils.query import insert_record, find_record
from utils.error import (
    ServiceError,
    StashBaseApiError,
    InvalidTokenError,
)

jwt_handler = JWTHandler(Config)
router = APIRouter(tags=["User General"], prefix="/user/general")


async def logout_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    user_token_record = await find_record(
        db=db, table=UserToken, unique_id=current_user.unique_id, order_by="desc"
    )
    blacklist_access_token = await find_record(
        db=db,
        table=BlacklistToken,
        access_token=user_token_record.access_token,
        order_by="desc",
    )
    blacklist_refresh_token = await find_record(
        db=db,
        table=BlacklistToken,
        refresh_token=user_token_record.refresh_token,
        order_by="desc",
    )

    try:
        if blacklist_access_token:
            raise InvalidTokenError(detail="Access token already blacklisted.")

        if blacklist_refresh_token:
            raise InvalidTokenError(detail="Refresh token already blacklisted.")

        if not (blacklist_refresh_token and blacklist_access_token):
            await insert_record(
                db=db,
                table=BlacklistToken,
                data={
                    "blacklisted_at": current_time,
                    "unique_id": current_user.unique_id,
                    "access_token": user_token_record.access_token,
                    "refresh_token": user_token_record.refresh_token,
                },
            )

        response.message = "Logout successful."
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
