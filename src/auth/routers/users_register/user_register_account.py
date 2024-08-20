from uuid_extensions import uuid7
from src.database.models import users
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.request_format import CreateUser
from src.auth.utils.database.general import local_time
from src.database.connection import database_connection
from fastapi import APIRouter, HTTPException, status
from src.auth.utils.database.general import (
    check_fullname,
    check_phone_number,
    is_using_registered_phone_number,
    extract_phone_number_otp,
    save_otp_phone_number_verification,
)

router = APIRouter(tags=["users-register"], prefix="/users")


async def register_user(schema: CreateUser) -> ResponseDefault:
    """
    Create a new users account with the following information:

    - **full_name**: The full name of the users.
    - **phone_number**: The phone number of the users.
        - Should be 10 - 13 digit of number.
    """

    response = ResponseDefault()

    try:
        user_uuid = str(uuid7())

        logging.info("Endpoint register account.")
        already_registered = await is_using_registered_phone_number(
            phone_number=schema.phone_number
        )

        if already_registered:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already created."
            )

        initial_data = await extract_phone_number_otp(user_uuid=user_uuid)

        logging.info("Creating new user.")
        validated_phone_number = await check_phone_number(
            phone_number=schema.phone_number
        )
        fullname = await check_fullname(value=schema.full_name)
        async with database_connection().connect() as session:
            try:
                query = users.insert().values(
                    user_uuid=user_uuid,
                    created_at=local_time(),
                    full_name=fullname,
                    phone_number=validated_phone_number,
                )
                await session.execute(query)
                await session.commit()
                logging.info("Created new account.")
                response.message = "Register account success."
                response.success = True
            except Exception as E:
                logging.error(f"Error during creating account: {E}.")
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Server error during creating account: {E}.",
                )
            finally:
                await session.close()

        if not initial_data:
            logging.info("Initialized OTP save data.")
            await save_otp_phone_number_verification(
                user_uuid=user_uuid,
                current_api_hit=1,
                saved_by_system=True,
                save_to_hit_at=local_time(),
            )

        response.success = True
        response.message = "Account successfully created."
        response.data = UniqueID(unique_id=user_uuid)

    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error after creating account: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/register",
    response_model=ResponseDefault,
    endpoint=register_user,
    status_code=status.HTTP_201_CREATED,
    summary="Account registration.",
)
