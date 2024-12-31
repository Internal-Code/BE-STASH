import httpx
from pytz import timezone
from sqlalchemy.sql import select
from fastapi import APIRouter, status
from datetime import timedelta, datetime
from utils.logger import logging
from src.secret import Config
from services.postgres.models import send_otps
from utils.jwt.general import get_user
from utils.validator import check_uuid
from utils.generator import random_number
from utils.database.general import local_time
from services.postgres.connection import database_connection
from utils.request_format import SendOTPPayload
from src.schema.response import ResponseDefault, UniqueID
from utils.custom_error import (
    ServiceError,
    FinanceTrackerApiError,
    EntityAlreadyVerifiedError,
    MandatoryInputError,
    EntityDoesNotExistError,
    InvalidOperationError,
)

config = Config()
router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_phone_number_endpoint(unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    check_uuid(unique_id=unique_id)

    now_utc = datetime.now(timezone("UTC"))
    account = await get_user(unique_id=unique_id)
    generated_otp = str(await random_number(6))

    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    select(send_otps)
                    .where(send_otps.c.user_uuid == unique_id)
                    .order_by(send_otps.c.created_at.desc())
                    .with_for_update()
                )

                result = await session.execute(query)

                latest_record = result.fetchone()

                if not latest_record:
                    logging.info("OTP data initialization not found.")
                    raise EntityDoesNotExistError(detail="Data not found.")

                jakarta_timezone = timezone("Asia/Jakarta")
                times_later_jakarta = latest_record.hit_tomorrow_at.astimezone(jakarta_timezone)
                formatted_time = times_later_jakarta.strftime("%Y-%m-%d %H:%M:%S")

                if not account.phone_number:
                    logging.info("User should filled phone number yet.")
                    raise MandatoryInputError(detail="User should fill phone number first.")

                if latest_record.current_api_hit % 4 == 0:
                    logging.info("User should only hit API again tomorrow.")
                    raise InvalidOperationError(
                        detail=f"Maximum API hit reached. You can try again after {formatted_time}."
                    )

                if now_utc < latest_record.save_to_hit_at:
                    logging.info("User should wait API cooldown.")
                    raise InvalidOperationError(
                        detail="Should wait in 1 minutes.",
                    )

                if not account:
                    logging.info("Data otp found.")
                    raise EntityDoesNotExistError(detail="Data not found.")

                if account.verified_phone_number:
                    logging.info("User phone number already verified.")
                    raise EntityAlreadyVerifiedError(detail="User phone number already verified.")

                if (
                    now_utc > latest_record.save_to_hit_at
                    and latest_record.current_api_hit % 4 != 0
                    or now_utc > latest_record.hit_tomorrow_at
                    and latest_record.current_api_hit % 4 == 0
                ):
                    logging.info("Matched condition. Sending OTP using whatsapp API.")
                    current_api_hit = (
                        latest_record.current_api_hit + 1 if latest_record.current_api_hit else 1
                    )
                    valid_per_day = (
                        send_otps.update()
                        .where(send_otps.c.user_uuid == unique_id)
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

                    payload = SendOTPPayload(
                        phoneNumber=account.phone_number,
                        message=f"""Your verification code is *{generated_otp}*. Please enter this code to complete your verification. Kindly note that this code will expire in 3 minutes.""",
                    )

                    async with httpx.AsyncClient() as client:
                        whatsapp_response = await client.post(
                            config.WHATSAPP_API_MESSAGE, json=dict(payload)
                        )

                    if whatsapp_response.status_code != 200:
                        raise ServiceError(
                            detail="Failed to send OTP via WhatsApp.",
                            name="Whatsapp API",
                        )

                    await session.execute(valid_per_day)
                    response.success = True
                    response.message = "OTP data sent to phone number."
                    response.data = UniqueID(unique_id=unique_id)

            except FinanceTrackerApiError as FTE:
                raise FTE

            except Exception as E:
                logging.error(f"Error during send otp email: {E}")
                raise ServiceError(
                    detail=f"Service error during send otp to phone number: {E}.",
                    name="Whatsapp API",
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
    path="/phone-number/{unique_id}",
    endpoint=send_otp_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="Send otp phone number.",
)
