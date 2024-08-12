from src.auth.utils.forgot_password.general import send_gmail
from pytz import timezone
from datetime import datetime
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import OTPVerification
from src.auth.utils.database.general import (
    extract_phone_number_otp_token,
    update_phone_number_status,
)
from src.auth.utils.jwt.general import get_user, get_password_hash
from src.auth.utils.generator import random_sso_username, random_password
from fastapi import APIRouter, status, HTTPException

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_otp_phone_number(
    otp: OTPVerification, unique_id: str
) -> ResponseDefault:
    response = ResponseDefault()

    try:
        initials_account = await extract_phone_number_otp_token(
            phone_number_token=unique_id
        )
        if not initials_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="UUID data not found."
            )

        now_utc = datetime.now(timezone("UTC"))
        if initials_account.blacklisted_at < now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="OTP already expired."
            )

        if initials_account.otp_number != otp.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code."
            )

        account = await get_user(identifier=initials_account.email)
        generated_username = random_sso_username(account.email)
        generated_password = random_password(8)
        hashed_generated_password = await get_password_hash(password=generated_password)

        email_body = (
            f"Dear {account.email},<br><br>"
            f"We are delighted to inform you that your account has been successfully registered in our application. Below are your username and password, which you can use to log in:<br><br>"
            f"You may log in using either your username or registered email address, along with the password provided below.<br><br>"
            f"<b>Username: {generated_username}</b><br>"
            f"<b>Password: {generated_password}</b><br><br>"
            f"For your security, we strongly recommend changing your password at your earliest convenience.<br><br>"
            f"Thank you for choosing our service.<br><br>"
            f"Best regards,<br>"
            f"The Support Team"
        )

        await update_phone_number_status(
            email=account.email, password=hashed_generated_password
        )
        await send_gmail(
            email_subject="Default Password",
            email_receiver=account.email,
            email_body=email_body,
        )

        response.success = True
        response.message = f"Account {account.email} phone number verified."

    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in verify_phone_number: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=verify_otp_phone_number,
    status_code=status.HTTP_200_OK,
    summary="User phone number verification.",
)
