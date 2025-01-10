from fastapi.templating import Jinja2Templates
from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.generator import random_number
from services.postgres.models import SendOtp
from utils.query.general import find_record, update_record
from src.schema.response import ResponseDefault
from utils.helper import local_time
from utils.jwt import get_current_user
from utils.smtp import send_gmail
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    InvalidOperationError,
)

router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_email_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)], db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    generated_otp = random_number(6)
    otp_record = await find_record(db=db, table=SendOtp, unique_id=current_user.unique_id)
    templates = Jinja2Templates(directory="templates")

    try:
        if not current_user.email:
            raise MandatoryInputError(detail="User should add email first.")

        if current_user.verified_email:
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_time < otp_record.save_to_hit_at:
            raise InvalidOperationError(detail="Should wait in 1 minutes.")

        if current_time > otp_record.save_to_hit_at:
            email_body = templates.TemplateResponse(
                "otp_email.html",
                context={
                    "request": {},
                    "full_name": current_user.full_name,
                    "otp": generated_otp,
                },
            ).body.decode("utf-8")

            await send_gmail(
                email_subject="OTP Email Verification.",
                email_receiver=current_user.email,
                email_body=email_body,
            )

            await update_record(
                db=db,
                table=SendOtp,
                conditions={"unique_id": current_user.unique_id},
                data={
                    "updated_at": current_time,
                    "otp_number": generated_otp,
                    "current_api_hit": otp_record.current_api_hit + 1 if otp_record.current_api_hit else 1,
                    "save_to_hit_at": current_time + timedelta(minutes=1),
                    "blacklisted_at": current_time + timedelta(minutes=3),
                },
            )

            response.message = f"OTP sent to {current_user.email}."

    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["POST"],
    path="/email",
    endpoint=send_otp_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send otp to validate user email.",
)
