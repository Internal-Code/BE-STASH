from src.auth.utils.logging import logging
from src.auth.utils.jwt.general import get_user
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import ChangeUserPhoneNumber
from src.auth.utils.database.general import (
    update_user_phone_number,
    verify_uuid,
    check_phone_number,
)
from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["users-register"], prefix="/users")


async def change_phone_number_endpoint(
    schema: ChangeUserPhoneNumber, unique_id: str
) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)
    await check_phone_number(phone_number=schema.phone_number)
    try:
        account = await get_user(unique_id=unique_id)
        registered_phone_number = await get_user(phone_number=schema.phone_number)

        if account.phone_number == schema.phone_number:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot changed into same phone number.",
            )

        if registered_phone_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already taken.",
            )

        if not account.full_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User should fill full name first.",
            )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found."
            )

        if account.pin is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account already set pin"
            )

        if account:
            logging.info("Update registered phone number.")
            await update_user_phone_number(
                user_uuid=unique_id, phone_number=schema.phone_number
            )
            response.success = True
            response.message = "Phone number successfully updated."
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
    path="/change-phone-number/{unique_id}",
    response_model=ResponseDefault,
    endpoint=change_phone_number_endpoint,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Change registered account phone number.",
)
