from typing import Annotated
from datetime import timedelta
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.smtp import send_gmail
from utils.time_utils import local_time
from utils.generator import Generator
from utils.query import QueryDatabase
from services.postgre.model import SendOtp
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    InvalidOperationError,
    DataNotFoundError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_email_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Send OTP email endpoint.")
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)
    generated_otp = generator.random_number(6)
    current_time = local_time()
    templates = Jinja2Templates(directory="templates")

    try:
        otp_record = await query.find(table=SendOtp, unique_id=current_user.unique_id)

        if not otp_record:
            logging.error("OTP record not found")
            raise DataNotFoundError("OTP record not found.")

        remaining_time = otp_record.save_to_hit_at.second - current_time.second

        if not current_user.email:
            logging.error("User is not add an email.")
            raise MandatoryInputError(detail="Should add email first.")

        if current_user.verified_email:
            logging.error("User email is not verified.")
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_time < otp_record.save_to_hit_at:
            logging.info(f"Should wait for API cooldown {remaining_time}s.")
            raise InvalidOperationError(detail=f"Should wait in {remaining_time}s.")

        if current_time > otp_record.save_to_hit_at:
            logging.info("Sending send otp into email.")
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

            response.message = f"OTP sent to {current_user.email}."

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/email",
    endpoint=send_otp_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send otp to validate user email.",
)
