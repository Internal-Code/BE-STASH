# TODO: Refactor this endpoint
from typing import Annotated
from utils.logger import logging
from utils.jwt import JWTHandler
from utils.helper import local_time
from utils.query import QueryDatabase
from services.postgres.models import User
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from src.schema.request_format import UpdateUserFullName
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def update_full_name_endpoint(
    schema: UpdateUserFullName,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)
    current_time = local_time()
    try:
        logging.info("Endpoint update full name.")
        await query.update(
            table=User,
            condition={"unique_id": current_user.unique_id},
            data={
                "full_name": schema.change_full_name_into,
                "updated_at": current_time,
            },
        )

        response.message = "Success update full name."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/full-name",
    endpoint=update_full_name_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user pin endpoint.",
)
