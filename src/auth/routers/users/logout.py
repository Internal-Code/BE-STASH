from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.jwt.general import get_current_user
from src.database.models import blacklist_tokens
from src.database.connection import database_connection
from src.auth.utils.database.general import (
    local_time,
    is_refresh_token_blacklisted,
    is_access_token_blacklisted,
    extract_tokens,
)

router = APIRouter(tags=["users-general"], prefix="/users")


async def user_logout(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    saved_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Token already blacklisted."
    )

    response = ResponseDefault()
    try:
        token_data = await extract_tokens(user_uuid=current_user.user_uuid)

        validate_refresh_token = await is_refresh_token_blacklisted(
            refresh_token=token_data.refresh_token
        )
        validate_access_token = await is_access_token_blacklisted(
            access_token=token_data.access_token
        )

        if validate_refresh_token is True or validate_access_token is True:
            raise saved_token

        async with database_connection().connect() as session:
            try:
                query = blacklist_tokens.insert().values(
                    blacklisted_at=local_time(),
                    user_uuid=current_user.user_uuid,
                    access_token=token_data.access_token,
                    refresh_token=token_data.refresh_token,
                )
                await session.execute(query)
                await session.commit()
                logging.info(f"User {current_user.username} logged out successfully.")
                response.message = "Logout successful."
                response.success = True
            except Exception as E:
                logging.error(f"Error during logout: {E}.")
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Server error during logout: {E}.",
                )
            finally:
                await session.close()
    except HTTPException as e:
        logging.error(f"HTTPException during logout: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Server error after logout: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/logout",
    response_model=ResponseDefault,
    endpoint=user_logout,
    status_code=status.HTTP_200_OK,
    summary="Logout logged in current user.",
)
