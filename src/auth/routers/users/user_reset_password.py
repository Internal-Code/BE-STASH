from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import ForgotPassword
from fastapi import APIRouter, HTTPException, status
from src.auth.utils.database.general import (
    verify_reset_id,
    reset_user_password,
    extract_reset_id,
)
from src.auth.utils.jwt.general import get_user, get_password_hash

router = APIRouter(tags=["users"], prefix="/users")


async def reset_password(request: ForgotPassword, unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    try:
        reset_id_is_valid = await verify_reset_id(reset_id=unique_id)
        if reset_id_is_valid is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset ID.",
            )

        if request.password != request.confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords is not match.",
            )

        user_email = await extract_reset_id(reset_id=unique_id)
        detail_user = await get_user(identifier=user_email.email)

        if not detail_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User {user_email.email} not found.",
            )
        hashed_password = await get_password_hash(password=request.password)
        await reset_user_password(
            user_uuid=detail_user.user_uuid, changed_password=hashed_password
        )

        response.success = True
        response.message = "Password successfully reset."
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Server error resetting password: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/reset-password/{unique_id}",
    response_model=ResponseDefault,
    endpoint=reset_password,
    status_code=status.HTTP_200_OK,
    summary="Create new password.",
)
