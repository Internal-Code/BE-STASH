from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.helper import local_time
from utils.query import QueryDatabase
from services.postgres.models import User
from src.schema.request_format import Email
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from utils.error import (
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
)


router = APIRouter(tags=["User Detail"], prefix="/user/detail")
jwt_handler = JWTHandler()


async def add_email_endpoint(
    schema: Email,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Add email endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    current_time = local_time()

    try:
        if schema.email != current_user.email:
            logging.warning("Using different email.")
            registered_email = await query.find(table=User, email=schema.email)
            if registered_email:
                logging.error("Email already exist.")
                raise EntityAlreadyExistError(
                    detail="Email already taken. Please use another email."
                )

        if current_user.email:
            logging.error("Email already registered by user.")
            raise EntityAlreadyExistError(detail="User already registered email.")

        await query.update(
            table=User,
            condition={"unique_id": current_user.unique_id},
            data={"email": schema.email, "updated_at": current_time},
        )

        response.message = "New email successfully added."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/add-email",
    response_model=ResponseDefault,
    endpoint=add_email_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="User add new email.",
)
