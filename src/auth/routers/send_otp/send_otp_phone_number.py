from pytz import timezone
from datetime import timedelta, datetime
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.generator import random_number
from src.auth.utils.jwt.general import get_user
from fastapi import APIRouter, status, HTTPException
from src.database.models import send_otps
from sqlalchemy.sql import select
from src.database.connection import database_connection
from src.auth.utils.database.general import (
    local_time,
    verify_uuid,
)

router = APIRouter(tags=["send-otp"], prefix="/send-otp")


async def send_otp_phone_number_endpoint(unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    now_utc = datetime.now(timezone("UTC"))
    account = await get_user(unique_id=unique_id)
    generated_otp = str(await random_number(6))
    await verify_uuid(unique_id=unique_id)

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
                jakarta_timezone = timezone("Asia/Jakarta")
                times_later_jakarta = latest_record.hit_tomorrow_at.astimezone(
                    jakarta_timezone
                )
                formatted_time = times_later_jakarta.strftime("%Y-%m-%d %H:%M:%S")

                if (
                    now_utc > latest_record.save_to_hit_at
                    and latest_record.current_api_hit % 4 != 0
                    or now_utc > latest_record.hit_tomorrow_at
                    and latest_record.current_api_hit % 4 == 0
                ):
                    logging.info("Matched condition. Sending OTP using whatsapp API.")
                    current_api_hit = (
                        latest_record.current_api_hit + 1
                        if latest_record.current_api_hit
                        else 1
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

                    # payload = SendOTPPayload(
                    #     phoneNumber=account.phone_number,
                    #     message=f"""Your verification code is *{generated_otp}*. Please enter this code to complete your verification. Kindly note that this code will expire in 3 minutes.""",
                    # )

                    # async with httpx.AsyncClient() as client:
                    #     whatsapp_response = await client.post(
                    #         LOCAL_WHATSAPP_API, json=dict(payload)
                    #     )

                    # if whatsapp_response.status_code != 200:
                    #     raise HTTPException(
                    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    #         detail="Failed to send OTP via WhatsApp.",
                    #     )

                    await session.execute(valid_per_day)
                    response.success = True
                    response.message = "OTP data sent to phone number."
                    response.data = UniqueID(unique_id=unique_id)

                if latest_record.current_api_hit % 4 == 0:
                    logging.info("User should only hit API again tomorrow.")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Maximum API hit reached. You can try again after {formatted_time}.",
                    )

                if now_utc < latest_record.save_to_hit_at:
                    logging.info("User should wait API cooldown.")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Should wait in 1 minutes.",
                    )

                if not account:
                    logging.info("Data otp found.")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Data not found."
                    )

                if account.verified_phone_number:
                    logging.info("User phone number already verified.")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User phone number already verified.",
                    )

            except HTTPException as E:
                raise E
            except Exception as E:
                logging.error(f"Exception error during send otp phone number: {E}")
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Server error during send otp phone number: {E}.",
                )
            finally:
                await session.commit()
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in send_otp_phone_number_endpoint: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=send_otp_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="Send otp phone number.",
)
