from pytz import timezone
from typing import Annotated
from sqlalchemy.sql import select
from datetime import timedelta, datetime
from services.postgres.models import send_otps
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from utils.generator import random_number
from src.schema.response import ResponseDefault
from utils.database.general import local_time
from services.postgres.connection import database_connection
from utils.jwt.general import get_current_user
from utils.forgot_password.general import send_gmail
from utils.custom_error import (
    ServiceError,
    FinanceTrackerApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    InvalidOperationError,
)

router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_email_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    now_utc = datetime.now(timezone("UTC"))
    generated_otp = str(await random_number(6))

    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    select(send_otps)
                    .where(send_otps.c.user_uuid == current_user.user_uuid)
                    .order_by(send_otps.c.created_at.desc())
                    .with_for_update()
                )

                result = await session.execute(query)
                latest_record = result.fetchone()
                jakarta_timezone = timezone("Asia/Jakarta")
                times_later_jakarta = latest_record.hit_tomorrow_at.astimezone(
                    jakarta_timezone
                )
                formatted_time = times_later_jakarta.strftime("%Y-%m-%d %H:%M:%S")

                if not current_user.email:
                    logging.info("User is not filled email yet.")
                    raise MandatoryInputError(detail="User should add email first.")

                if latest_record.current_api_hit % 4 == 0:
                    logging.info("User should only hit API again tomorrow.")
                    raise InvalidOperationError(
                        detail=f"Maximum API hit reached. You can try again after {formatted_time}."
                    )

                if now_utc < latest_record.save_to_hit_at:
                    logging.info("User should wait API cooldown.")
                    raise InvalidOperationError(detail="Should wait in 1 minutes.")

                if current_user.verified_email:
                    logging.info("User email  already verified.")
                    raise EntityAlreadyVerifiedError(
                        detail="User email already verified."
                    )

                if (
                    now_utc > latest_record.save_to_hit_at
                    and latest_record.current_api_hit % 4 != 0
                    or now_utc > latest_record.hit_tomorrow_at
                    and latest_record.current_api_hit % 4 == 0
                ):
                    logging.info("Matched condition. Sending OTP using email services.")
                    current_api_hit = (
                        latest_record.current_api_hit + 1
                        if latest_record.current_api_hit
                        else 1
                    )
                    valid_per_day = (
                        send_otps.update()
                        .where(send_otps.c.user_uuid == current_user.user_uuid)
                        .values(
                            updated_at=local_time(),
                            otp_number=generated_otp,
                            current_api_hit=current_api_hit,
                            saved_by_system=False,
                            save_to_hit_at=local_time() + timedelta(minutes=1),
                            blacklisted_at=local_time() + timedelta(minutes=3),
                            hit_tomorrow_at=local_time() + timedelta(days=1),
                        )
                    )

                    email_body = (
                        f"Dear <b>{current_user.full_name}</b>,<br><br>"
                        f"We received a request to verify email address. Please enter the following code to verify your account:<br><br>"
                        f"Your verification code is <b>{generated_otp}</b>. Please enter this code to complete your verification<br><br>"
                        f"Please note, that this code will expire in <b>3 minutes</b>.<br>"
                        f"Thank you,<br><br>"
                        f"Best regards,<br>"
                        f"<b>Support Team</b>"
                    )

                    await send_gmail(
                        email_subject="OTP Email Verification.",
                        email_receiver=current_user.email,
                        email_body=email_body,
                    )

                    await session.execute(valid_per_day)
                    response.success = True
                    response.message = "OTP data sent to email."

            except FinanceTrackerApiError as FTE:
                raise FTE

            except Exception as E:
                logging.error(f"Error during send otp email: {E}")
                raise ServiceError(
                    detail=f"Service error during send otp email: {E}.",
                    name="Google SMTP",
                )
            finally:
                await session.commit()
                await session.close()
    except FinanceTrackerApiError as FTE:
        raise FTE

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
