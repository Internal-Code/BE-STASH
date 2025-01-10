from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from src.schema.request_format import UpdateUserFullName
from utils.helper import local_time
from utils.query.general import update_record
from services.postgres.models import User
from utils.custom_error import (
    DatabaseQueryError,
    ServiceError,
    StashBaseApiError,
)

router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def change_full_name_endpoint(
    schema: UpdateUserFullName,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    try:
        logging.info("Endpoint update full name.")
        await update_record(
            db=db,
            table=User,
            conditions={"unique_id": current_user.unique_id},
            data={"full_name": schema.change_full_name_into, "updated_at": current_time},
        )

        response.success = True
        response.message = "Success changed full name."

    except StashBaseApiError:
        raise
    except DatabaseQueryError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/full-name",
    endpoint=change_full_name_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user pin endpoint.",
)
