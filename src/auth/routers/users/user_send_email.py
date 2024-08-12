import pytz
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import SendVerificationLink, SendForgotPasswordMethod
from src.auth.utils.database.general import verify_reset_id, extract_reset_id
from src.auth.utils.forgot_password.general import send_gmail
from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["users"], prefix="/users")


async def send_email_endpoints(request: SendVerificationLink) -> ResponseDefault:
    response = ResponseDefault()
    try:
        registered_user = await verify_reset_id(request.reset_id)
        if not registered_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset ID.",
            )

        change_password_user = await extract_reset_id(reset_id=request.reset_id)

        if request.forget_password_type == SendForgotPasswordMethod.EMAIL:
            reset_link = (
                f"http://localhost:8000/api/v1/users/reset-password/{request.reset_id}"
            )

            jakarta_tz = pytz.timezone("Asia/Jakarta")
            expiration_time = change_password_user.expired_at.astimezone(jakarta_tz)
            formatted_expiration_time = expiration_time.strftime("%Y-%m-%d %H:%M:%S")

            email_body = (
                f"Dear {change_password_user.email},\n\n"
                f"We received a request to reset your password. Please click the link below to create a new password:\n\n"
                f"{reset_link}\n\n"
                f"This link will expire on {formatted_expiration_time}. If you did not request a password reset, please ignore this email.\n\n"
                f"Thank you,\n\n"
                f"Best regards,"
                f"The Support Team"
            )

            await send_gmail(
                email_subject="Reset Password",
                email_receiver=change_password_user.email,
                email_body=email_body,
            )

        response.success = True
        response.message = f"Password reset link sent to {change_password_user.email}."

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
    path="/send-email",
    response_model=ResponseDefault,
    endpoint=send_email_endpoints,
    status_code=status.HTTP_200_OK,
    summary="Send email confirmation to forgot password.",
)
