from uuid import UUID
from uuid_extensions import uuid7
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import InputPhoneNumber
from src.auth.utils.database.general import (
    save_phone_number,
    extract_phone_number_token,
    check_phone_number,
    is_using_registered_phone_number,
    save_otp_phone_number_verification,
)
from fastapi import APIRouter, status, HTTPException

router = APIRouter(tags=["users"], prefix="/users")


async def save_phone_number_endpoint(
    phone_number: InputPhoneNumber, phone_number_id: str
) -> ResponseDefault:
    response = ResponseDefault()

    try:
        UUID(phone_number_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format.",
        )

    try:
        phone_number_otp_unique_id = str(uuid7())

        account = await extract_phone_number_token(
            phone_number_unique_id=phone_number_id
        )
        logging.info("UUID found.")
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="UUID not found."
            )

        validated_phone_number = await check_phone_number(
            value=phone_number.phone_number
        )
        registered_phone_number = await is_using_registered_phone_number(
            phone_number=validated_phone_number
        )

        if registered_phone_number:
            logging.info("Phone number already saved.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already used. Please use another number.",
            )

        await save_phone_number(
            email=account.email, phone_number=validated_phone_number
        )
        await save_otp_phone_number_verification(
            phone_number_otp_uuid=phone_number_otp_unique_id, email=account.email
        )

        response.success = True
        response.message = "Phone number saved."
        response.data = {"otp_id": phone_number_otp_unique_id}

    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in save_phone_number: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{phone_number_id}",
    endpoint=save_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Verify phone number.",
)
