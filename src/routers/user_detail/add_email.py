from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.request_format import UserEmail
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from utils.query import QueryDatabase
from services.postgres.models import User
from src.secret import Config
from utils.helper import local_time
from utils.jwt import JWTHandler
from utils.error import (
    EntityAlreadyVerifiedError,
    EntityAlreadyExistError,
    EntityForceInputSameDataError,
    ServiceError,
    StashBaseApiError,
)


router = APIRouter(tags=["User Detail"], prefix="/user/detail")
jwt_handler = JWTHandler(Config)


async def add_email_endpoint(
    schema: UserEmail,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)

    current_time = local_time()
    registered_email = await query.find(table=User, email=schema.email)
    user_record = await query.find(table=User, unique_id=current_user.unique_id)

    try:
        if registered_email:
            raise EntityAlreadyExistError(
                detail="Email already taken. Please use another email."
            )

        if user_record.verified_email:
            raise EntityAlreadyVerifiedError(
                detail="User already have an verified email."
            )

        if user_record.email:
            raise EntityAlreadyExistError(detail="User already have an email.")

        if user_record.email == schema.email:
            raise EntityForceInputSameDataError(detail="Cannot update into same email.")

        await query.update(
            table=User,
            condition={"unique_id": current_user.unique_id},
            data={"email": schema.email, "updated_at": current_time},
        )

        response.message = "Success add new email."

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
