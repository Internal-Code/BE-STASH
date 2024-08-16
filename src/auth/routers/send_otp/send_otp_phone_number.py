import httpx
from pytz import timezone
from datetime import timedelta, datetime
from src.secret import LOCAL_WHATSAPP_API
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.generator import random_number
from src.auth.utils.request_format import SendOTPPayload
from src.auth.utils.jwt.general import get_user
from fastapi import APIRouter, status, HTTPException
from src.auth.utils.database.general import (
    extract_phone_number_otp_token,
    save_otp_phone_number_verification,
    verify_uuid,
)

router = APIRouter(tags=["send-otp"], prefix="/send-otp")


async def send_otp_phone_number_endpoint(unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)

    try:
        latest_data = await extract_phone_number_otp_token(user_uuid=unique_id)
        account = await get_user(unique_id=unique_id)
        otp_number = str(random_number(6))

        if account.verified_phone_number:
            logging.info("User phone number already verified.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account phone number already verified.",
            )

        logging.info("User phone number is not verified.")
        payload = SendOTPPayload(
            phoneNumber=account.phone_number,
            message=f"""Your verification code is *{otp_number}*. Please enter this code to complete your verification. Kindly note that this code will expire in 5 minutes.""",
        )

        if latest_data is None:
            logging.info("Initialized send OTP API hit.")
            async with httpx.AsyncClient() as client:
                whatsapp_response = await client.post(
                    LOCAL_WHATSAPP_API, json=dict(payload)
                )

            if whatsapp_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send OTP via WhatsApp.",
                )

            await save_otp_phone_number_verification(
                phone_number_otp_uuid=unique_id,
                phone_number=account.phone_number,
                otp_number=otp_number,
            )

            response.success = True
            response.message = "Initialized send OTP data."
            response.data = UniqueID(unique_id=unique_id)
            return response

        now_utc = datetime.now(timezone("UTC"))
        jakarta_timezone = timezone("Asia/Jakarta")
        save_to_hit_at = now_utc + timedelta(minutes=1)
        if latest_data.save_to_hit_at is None:
            valid_save_to_hit_at = save_to_hit_at
        else:
            valid_save_to_hit_at = latest_data.save_to_hit_at
        times_later_jakarta = valid_save_to_hit_at.astimezone(jakarta_timezone)
        formatted_time = times_later_jakarta.strftime("%Y-%m-%d %H:%M:%S")

        if latest_data is not None and now_utc < valid_save_to_hit_at:
            logging.info("User should wait API cooldown.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Should wait until {formatted_time}.",
            )

        if now_utc > valid_save_to_hit_at:
            logging.info("Saved new reset pin request data.")
            async with httpx.AsyncClient() as client:
                whatsapp_response = await client.post(
                    LOCAL_WHATSAPP_API, json=dict(payload)
                )

            if whatsapp_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send OTP via WhatsApp.",
                )

            await save_otp_phone_number_verification(
                phone_number_otp_uuid=unique_id,
                phone_number=account.phone_number,
                otp_number=otp_number,
            )

            response.success = True
            response.message = "OTP data sent to phone number."
            response.data = UniqueID(unique_id=unique_id)

            return response
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in verify_phone_number: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=send_otp_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send otp phone number.",
)
