from fastapi.templating import Jinja2Templates
from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.generator import random_number
from services.postgres.models import SendOtp, User
from utils.query.general import find_record, update_record
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import UserEmail
from utils.helper import local_time
from utils.jwt import get_current_user
from utils.smtp import send_gmail
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    InvalidOperationError,
    EntityForceInputSameDataError,
)

router = APIRouter(tags=["User Wrong Account"], prefix="/user/wrong")


async def wrong_email_endpoint(
    schema: UserEmail,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
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

        if current_user.email == schema.email:
            raise EntityForceInputSameDataError(detail="Cannot changed into same email.")

        if current_time < otp_record.save_to_hit_at:
            raise InvalidOperationError(detail="Should wait in 1 minutes.")

        if current_time > otp_record.save_to_hit_at:
            email_body = templates.TemplateResponse(
                "otp_email.html",
                context={"request": {}, "full_name": current_user.full_name, "otp": generated_otp},
            ).body.decode("utf-8")

            background_tasks.add_task(
                send_gmail,
                email_subject="OTP Email Verification.",
                email_receiver=schema.email,
                email_body=email_body,
            )

            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": current_user.unique_id},
                data={
                    "updated_at": current_time,
                    "email": schema.email,
                },
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

            response.message = f"OTP sent to {schema.email}."
            response.data = UniqueId(unique_id=current_user.unique_id)

    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/email",
    endpoint=wrong_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send otp to validate user email.",
)
