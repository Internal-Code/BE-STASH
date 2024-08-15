from src.auth.utils.logging import logging
from src.auth.utils.jwt.general import get_user
from src.auth.schema.response import ResponseDefault, UniqueID
from fastapi import APIRouter, HTTPException, status
from src.auth.utils.database.general import (
    check_phone_number,
    save_reset_pin_data,
    extract_reset_pin_data,
)

router = APIRouter(tags=["users"], prefix="/users")


async def get_user_forgot_pin_endpoint(phone_number: str) -> ResponseDefault:
    response = ResponseDefault()
    try:
        validated_phone_number = await check_phone_number(phone_number=phone_number)
        account = await get_user(phone_number=validated_phone_number)

        if not account:
            logging.info("User not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        initial_data = await extract_reset_pin_data(user_uuid=account.user_uuid)

        if initial_data is not None:
            logging.info("Forgot pin data already initialized.")
            response.success = True
            response.message = "User already initialized forgot pin. Please choose send forgot link method."
            response.data = UniqueID(unique_id=str(account.user_uuid))

            return response

        logging.info("Save forgot pin initialization data.")
        await save_reset_pin_data(user_uuid=account.user_uuid)

        response.success = True
        response.message = f"User {validated_phone_number} found."
        response.data = UniqueID(unique_id=str(account.user_uuid))

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Server error after get_user_forgot_pin_endpoint: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )
    return response


router.add_api_route(
    methods=["GET"],
    path="/get-user/forgot-pin",
    response_model=ResponseDefault,
    endpoint=get_user_forgot_pin_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get unique id user forgot pin.",
)
