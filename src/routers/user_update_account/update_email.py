from typing import Annotated
from utils.logger import logging
from utils.helper import local_time
from utils.jwt import get_current_user
from services.postgres.models import User
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.request_format import UserEmail
from src.schema.response import ResponseDefault
from utils.query.general import find_record, update_record
from utils.custom_error import (
    EntityForceInputSameDataError,
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
)


router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def update_email_endpoint(
    schema: UserEmail,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    registered_email = await find_record(db=db, table=User, email=schema.email)

    try:
        pass
        if not current_user.email:
            logging.info("User is not input email yet.")
            raise MandatoryInputError(detail="User should add email first.")

        if not current_user.verified_email:
            raise MandatoryInputError(detail="User email should be verified first.")

        if current_user.email == schema.email:
            raise EntityForceInputSameDataError(detail="Cannot use same email.")

        if registered_email:
            raise EntityAlreadyExistError(detail="Email already taken. Please use another email.")

        await update_record(
            db=db,
            table=User,
            conditions={"unique_id": current_user.unique_id},
            data={"updated_at": current_time, "email": schema.email, "verified_email": False},
        )

        response.message = "Update email success."

    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    endpoint=update_email_endpoint,
    status_code=status.HTTP_200_OK,
    response_model=ResponseDefault,
    summary="Change user email.",
)
