from typing import Annotated
from src.auth.utils.logging import logging
from src.auth.utils.jwt.general import get_current_user
from fastapi import APIRouter, status, Depends, HTTPException
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.request_format import ChangeUserPhoneNumber
from src.auth.utils.database.general import (
    local_time,
    check_phone_number,
    is_using_registered_phone_number,
    update_user_phone_number,
    save_otp_phone_number_verification,
    extract_phone_number_otp,
)

router = APIRouter(tags=["account-verification"], prefix="/change")


async def change_phone_number_endpoint(
    schema: ChangeUserPhoneNumber,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()

    validated_phone_number = await check_phone_number(phone_number=schema.phone_number)
    registered_phone_number = await is_using_registered_phone_number(
        phone_number=validated_phone_number
    )
    initial_data = await extract_phone_number_otp(user_uuid=current_user.user_uuid)

    try:
        if validated_phone_number == current_user.phone_number:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot use same phone number.",
            )

        if registered_phone_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already used.",
            )

        logging.info("Updating user phone number.")
        await update_user_phone_number(
            user_uuid=current_user.user_uuid, phone_number=validated_phone_number
        )

        if not initial_data:
            logging.info("Initialized OTP save data.")
            await save_otp_phone_number_verification(
                user_uuid=current_user.user_uuid,
                current_api_hit=1,
                saved_by_system=True,
                save_to_hit_at=local_time(),
            )

        response.success = True
        response.message = "Update phone number success."
        response.data = UniqueID(unique_id=current_user.user_uuid)

    except HTTPException as E:
        raise E
    except Exception as E:
        raise E

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number",
    endpoint=change_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user valid phone number endpoint.",
)
