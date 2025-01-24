from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.smtp import send_gmail
from utils.helper import local_time
from utils.query import QueryDatabase
from utils.generator import Generator
from services.postgres.models import User
from fastapi.templating import Jinja2Templates
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.request_format import UserEmail
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    EntityForceInputSameDataError,
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
)


jwt_handler = JWTHandler()
router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def update_email_endpoint(
    schema: UserEmail,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)
    generator = Generator()
    current_time = local_time()

    generated_otp = generator.random_number(6)

    templates = Jinja2Templates(directory="templates")

    try:
        if not current_user.email:
            logging.info("User is not input email yet.")
            raise MandatoryInputError(detail="User should add email first.")

        if current_user.email != schema.email:
            registered_email = await query.find(table=User, email=schema.email)
            if registered_email:
                raise EntityAlreadyExistError(
                    detail="Email already taken. Please use another email."
                )

        if not current_user.verified_email:
            raise MandatoryInputError(detail="User email should be verified first.")

        if current_user.email == schema.email:
            raise EntityForceInputSameDataError(detail="Cannot use same email.")

        email_body = templates.TemplateResponse(
            "otp_email.html",
            context={
                "request": {},
                "full_name": current_user.full_name,
                "otp": generated_otp,
            },
        ).body.decode("utf-8")

        background_tasks.add_task(
            send_gmail,
            email_subject="OTP Email Verification.",
            email_receiver=current_user.email,
            email_body=email_body,
        )

        await query.update(
            table=User,
            condition={"unique_id": current_user.unique_id},
            data={
                "updated_at": current_time,
                "email": schema.email,
                "otp_state": False,
                "verified_email": False,
            },
        )

        response.message = "Success update email."

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    endpoint=update_email_endpoint,
    status_code=status.HTTP_200_OK,
    response_model=ResponseDefault,
    summary="Change user email.",
)
