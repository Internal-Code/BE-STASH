from src.auth.utils.logging import logging
from src.auth.utils.jwt.general import get_user, get_password_hash
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import UserPin
from src.auth.utils.database.general import update_user_pin, verify_uuid, check_pin
from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["users-register"], prefix="/users")


async def create_user_pin(pin: UserPin, unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)
    try:
        account = await get_user(unique_id=unique_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found."
            )

        if account.verified_phone_number is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User should validate phone number first.",
            )

        if account.pin is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account already set pin"
            )

        validated_pin = await check_pin(pin=pin.pin)
        hashed_pin = await get_password_hash(password=validated_pin)
        await update_user_pin(user_uuid=unique_id, pin=hashed_pin)

        # payload = SendOTPPayload(
        #     phoneNumber=account.phone_number,
        #     message=(
        #         f"Dear *{account.full_name}*,\n\n"
        #         "We are pleased to inform you that your phone number has been successfully verified. "
        #         "You can now log in using the following credentials:\n\n"
        #         f"Phone Number: *{account.phone_number}*\n"
        #         f"PIN: *{validated_pin}*\n\n"
        #         "Please ensure that you keep your account information secure.\n\n"
        #         "Best Regards,\n"
        #         "*Support Team*"
        #     ),
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

        response.success = True
        response.message = "Pin successfully added."
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Server error creating user pin: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/create-pin/{unique_id}",
    response_model=ResponseDefault,
    endpoint=create_user_pin,
    status_code=status.HTTP_201_CREATED,
    summary="Create user pin.",
)
