from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.request_format import GoogleSSOPayload
from src.auth.utils.jwt.general import get_user
from src.auth.utils.database.general import (
    update_user_google_sso,
    check_phone_number,
    is_using_registered_phone_number,
    verify_uuid,
    check_fullname,
)
from fastapi import APIRouter, status, HTTPException

router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_save_phone_number_endpoint(
    schema: GoogleSSOPayload, unique_id: str
) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)

    try:
        account = await get_user(unique_id=unique_id)
        logging.info("UUID found.")
        if not account:
            logging.info("UUID not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="UUID not found."
            )

        validated_phone_number = await check_phone_number(
            phone_number=schema.phone_number
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

        fullname = await check_fullname(value=schema.full_name)

        await update_user_google_sso(
            user_uuid=unique_id, phone_number=validated_phone_number, full_name=fullname
        )

        response.success = True
        response.message = "Updated full name and phone number."
        response.data = UniqueID(unique_id=unique_id)

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
    path="/account/{unique_id}",
    endpoint=google_sso_save_phone_number_endpoint,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Verify phone number google sso.",
)
