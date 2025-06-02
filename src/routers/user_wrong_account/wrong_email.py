from typing import Annotated
from datetime import timedelta
from utils.jwt import JWTHandler
from utils.smtp import send_gmail
from utils.logger import logging
from utils.helper import local_time
from utils.generator import Generator
from utils.query import QueryDatabase
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from src.schema.request_format import Email
from services.postgre.model import SendOtp, User
from src.schema.response import ResponseDefault, UniqueId
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    InvalidOperationError,
    EntityForceInputSameDataError,
    EntityAlreadyExistError,
    DataNotFoundError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Wrong Account"], prefix="/user/wrong")


async def wrong_email_endpoint(
    schema: Email,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Wrong email endpoint.")
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)
    current_time = local_time()
    generated_otp = generator.random_number(6)
    otp_record = await query.find(table=SendOtp, unique_id=current_user.unique_id)
    templates = Jinja2Templates(directory="templates")

    try:
        if not otp_record:
            logging.error("OTP record not found")
            raise DataNotFoundError("OTP record not found.")

        remaining_time = otp_record.save_to_hit_at.second - current_time.second

        if schema.email != current_user.email:
            registered_email = await query.find(table=User, email=schema.email)
            if registered_email:
                logging.error("Email already takeb.")
                raise EntityAlreadyExistError(
                    detail="Email already taken. Please use another email."
                )

        if not current_user.email:
            logging.error("User is not add an email.")
            raise MandatoryInputError(detail="Should add email first.")

        if current_user.verified_email:
            logging.error("User email is not verified.")
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_user.email == schema.email:
            logging.error("Cannot update into same email.")
            raise EntityForceInputSameDataError(
                detail="Should updated into different email."
            )

        if current_time < otp_record.save_to_hit_at:
            logging.info(f"Should wait for API cooldown {remaining_time}s.")
            raise InvalidOperationError(detail=f"Should wait in {remaining_time}s.")

        if current_time > otp_record.save_to_hit_at:
            email_body = templates.TemplateResponse(
                "otp_email.html",
                context={
                    "request": {},
                    "full_name": current_user.full_name,
                    "otp": generated_otp,
                },
            ).body.decode("utf-8")

            logging.info(f"Sending OTP into {current_time.email}")
            background_tasks.add_task(
                send_gmail,
                email_subject="OTP Email Verification.",
                email_receiver=schema.email,
                email_body=email_body,
            )

            await query.update(
                table=User,
                condition={"unique_id": current_user.unique_id},
                data={
                    "updated_at": current_time,
                    "email": schema.email,
                },
            )

            await query.update(
                table=SendOtp,
                condition={"unique_id": current_user.unique_id},
                data={
                    "updated_at": current_time,
                    "otp_number": generated_otp,
                    "current_api_hit": otp_record.current_api_hit + 1
                    if otp_record.current_api_hit
                    else 1,
                    "save_to_hit_at": current_time + timedelta(minutes=1),
                    "blacklisted_at": current_time + timedelta(minutes=3),
                },
            )

            response.message = "OTP sent to email."
            response.data = UniqueId(unique_id=current_user.unique_id)

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    endpoint=wrong_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send otp to validate user email.",
)
