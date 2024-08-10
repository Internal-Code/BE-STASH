from uuid_extensions import uuid7
from src.database.models import users
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import CreateUser
from src.auth.utils.database.general import local_time
from src.auth.utils.database.general import (
    filter_user_register,
    check_password,
    check_phone_number,
    check_username,
)
from src.database.connection import database_connection
from src.auth.utils.jwt.security import get_password_hash
from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["users"], prefix="/users")


async def register_user(schema: CreateUser) -> ResponseDefault:
    """
    Create a new users account with the following information:

    - **first_name**: The first name of the users.
    - **last_name (optional)**: The last name of the users.
    - **username**: The username chosen by the users for logging in.
        - Contain at least 5 character.
    - **email**: The email address of the users.
    - **phone_number**: The phone number of the users.
        - Should be 10 - 13 digit of number.
    - **password**: The password chosen by the users for account security. It must:
        - Be at least 8 characters long.
        - Contain at least one uppercase letter.
        - Contain at least one lowercase letter.
        - Contain at least one digit.
        - Contain at least one special character.
    """

    response = ResponseDefault()
    try:
        await filter_user_register(username=schema.username, email=schema.email)

        await check_phone_number(schema.phone_number)
        await check_username(schema.username)
        await check_password(schema.password)

        logging.info("Endpoint register account.")
        async with database_connection().connect() as session:
            try:
                query = users.insert().values(
                    user_uuid=uuid7(),
                    created_at=local_time(),
                    username=schema.username,
                    first_name=schema.first_name,
                    last_name=schema.last_name,
                    email=schema.email,
                    phone_number=schema.phone_number,
                    password=await get_password_hash(schema.password),
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
