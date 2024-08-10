from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import ResetPasswordRequest, SendForgotPasswordMethod
from src.auth.utils.database.general import verify_reset_id, extract_reset_id
from src.auth.utils.email.general import send_email
from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["users"], prefix="/users")


async def reset_password(request: ResetPasswordRequest) -> ResponseDefault:
    response = ResponseDefault()
    try:
        # Verify that the reset ID is valid and not expired
        registered_user = await verify_reset_id(request.reset_id)
        print("status registered user", registered_user)
        if registered_user is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset ID.",
            )

        change_password_user = await extract_reset_id(reset_id=request.reset_id)
        print(change_password_user)

        if request.forget_password_type == SendForgotPasswordMethod.EMAIL:
            # Send reset email
            reset_link = (
                f"https://localhost:8000/api/v1/users/reset-password/{request.reset_id}"
            )
            email_body = (
                f"Click the following link to reset your password: {reset_link}"
            )
            await send_email(
                subject="Reset Your Password",
                recipient=[change_password_user.email],
                message=email_body,
            )

            response.success = True
            response.message = (
                f"Password reset link sent to {change_password_user.email}."
            )

        # Additional handling for phone_number can be implemented later
    except HTTPException as e:
        logging.error(f"Error while resetting password: {e}.")
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
    path="/reset-password",
    response_model=ResponseDefault,
    endpoint=reset_password,
    status_code=status.HTTP_200_OK,
    summary="Reset user password",
)
