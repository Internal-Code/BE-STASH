import httpx
from src.secret import LOCAL_WHATSAPP_API
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.generator import random_number
from src.auth.utils.request_format import SendOTPPayload
from src.auth.utils.database.general import (
    extract_phone_number_otp_token,
    save_otp_phone_number_verification,
)
from src.auth.utils.jwt.general import get_user
from fastapi import APIRouter, status, HTTPException

router = APIRouter(tags=["send-otp"], prefix="/send-otp")


async def send_otp_phone_number(otp_id: str) -> ResponseDefault:
    response = ResponseDefault()

    try:
        otp_number = str(random_number(6))

        initials_account = await extract_phone_number_otp_token(
            phone_number_token=otp_id
        )
        if not initials_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="UUID data not found."
            )

        current_api_hit = (
            initials_account.current_api_hit + 1
            if initials_account.current_api_hit
            else 1
        )

        if current_api_hit > 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OTP maximum request reached. You should try again tomorrow.",
            )

        account = await get_user(identifier=initials_account.email)

        await save_otp_phone_number_verification(
            phone_number_otp_uuid=otp_id,
            email=account.email,
            current_api_hit=current_api_hit,
            otp_number=otp_number,
        )

        payload = SendOTPPayload(
            phoneNumber=account.phone_number,
            message=f"""Your verification code is *{otp_number}*. Please enter this code to complete your verification. Kindly note that this code will expire in 5 minutes.""",
        )

        async with httpx.AsyncClient() as client:
            whatsapp_response = await client.post(
                LOCAL_WHATSAPP_API, json=dict(payload)
            )
            print(whatsapp_response.status_code)

        if whatsapp_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP via WhatsApp.",
            )

        response.success = True
        response.message = "OTP data sent."
        response.data = {"verification_id": otp_id}

    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in verify_phone_number: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{otp_id}",
    endpoint=send_otp_phone_number,
    status_code=status.HTTP_201_CREATED,
    summary="Send otp phone number.",
)
