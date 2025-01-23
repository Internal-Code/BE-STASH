from src.secret import Config
from utils.jwt import JWTHandler
from typing import Annotated
from datetime import timedelta
from utils.smtp import send_gmail
from utils.helper import local_time
from utils.generator import Generator
from utils.query import QueryDatabase
from services.postgres.models import SendOtp
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    InvalidOperationError,
)

jwt_handler = JWTHandler(Config)
router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_email_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)

    generated_otp = generator.random_number(6)
    current_time = local_time()

    otp_record = await query.find(table=SendOtp, unique_id=current_user.unique_id)
    templates = Jinja2Templates(directory="templates")

    try:
        if not current_user.email:
            raise MandatoryInputError(detail="Should add email first.")

        if current_user.verified_email:
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_time < otp_record.save_to_hit_at:
            raise InvalidOperationError(detail="Should wait in 1 minute.")

        if current_time > otp_record.save_to_hit_at:
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
