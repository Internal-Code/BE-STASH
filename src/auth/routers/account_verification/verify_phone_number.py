from pytz import timezone
from datetime import datetime
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import OTPVerification
from src.auth.utils.jwt.general import get_user
from fastapi import APIRouter, status, HTTPException
from src.auth.utils.database.general import (
    extract_phone_number_otp,
    update_phone_number_status,
    verify_uuid,
    check_otp,
)

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_otp_phone_number(
    otp: OTPVerification, unique_id: str
) -> ResponseDefault:
    response = ResponseDefault()

    try:
        await verify_uuid(unique_id=unique_id)

        initials_account = await extract_phone_number_otp(phone_number_token=unique_id)
        now_utc = datetime.now(timezone("UTC"))

        if not initials_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="UUID data not found."
            )

        if now_utc > initials_account.blacklisted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token already expired."
            )

        account = await get_user(phone_number=initials_account.phone_number)

        if not account.verified_phone_number:
            logging.info("User phone number not verified.")

            await check_otp(otp=otp.otp)

            if now_utc > initials_account.blacklisted_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OTP already expired.",
                )

            if initials_account.otp_number != otp.otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code."
                )

            if initials_account.otp_number == otp.otp:
                await update_phone_number_status(user_uuid=unique_id)

                response.success = True
                response.message = "Account phone number verified."
                response.data = {"unique_id": unique_id}
        else:
            logging.info("User phone number already verified.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account phone number already verified.",
            )

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

# from pytz import timezone
# from datetime import datetime
# from src.auth.utils.logging import logging
# from src.auth.schema.response import ResponseDefault
# from src.auth.utils.request_format import OTPVerification
# from src.auth.utils.forgot_password.general import send_gmail
# from src.auth.utils.jwt.general import get_user, get_password_hash
# from src.auth.utils.generator import random_sso_username, random_password
# from src.auth.utils.database.general import (
#     extract_phone_number_otp,
#     update_phone_number_status,
#     verify_uuid
# )
# from fastapi import APIRouter, status, HTTPException

# router = APIRouter(tags=["account-verification"], prefix="/verify")


# async def verify_otp_phone_number(otp: OTPVerification, verification_id: str) -> ResponseDefault:
#     response = ResponseDefault()

#     try:
#         await verify_uuid(unique_id=verification_id)

#         initials_account = await extract_phone_number_otp(phone_number_token=verification_id)

#         if not initials_account:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="UUID data not found."
#             )

#         now_utc = datetime.now(timezone("UTC"))

#         if now_utc > initials_account.blacklisted_at:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, detail="OTP already expired."
#             )

#         if initials_account.otp_number != otp.otp:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code."
#             )

#         account = await get_user(phone_number=initials_account.phone_number)
#         generated_username = random_sso_username(account.email)
#         generated_password = random_password(8)
#         hashed_generated_password = await get_password_hash(password=generated_password)

#         await update_phone_number_status(
#             username=generated_username,
#             email=account.email,
#             password=hashed_generated_password,
#         )

#         if account.verified_email is True:
#             logging.info("User email is verified.")
#             email_body = (
#                 f"Dear {account.email},<br><br>"
#                 f"We are delighted to inform you that your account has been successfully registered in our application. Below are your username and password, which you can use to log in:<br><br>"
#                 f"You may log in using either your username or registered email address, along with the password provided below.<br><br>"
#                 f"<b>Username: {generated_username}</b><br>"
#                 f"<b>Password: {generated_password}</b><br><br>"
#                 f"For your security, we strongly recommend changing your password at your earliest convenience.<br><br>"
#                 f"Thank you for choosing our service.<br><br>"
#                 f"Best regards,<br>"
#                 f"The Support Team"
#             )

#             await send_gmail(
#                 email_subject="Default Password",
#                 email_receiver=account.email,
#                 email_body=email_body,
#             )

#             response.success = True
#             response.message = f"Account {account.email} phone number verified."
#         else:
#             logging.info("User email is not verified.")
#             response.success = True
#             response.message = f"Account {account.email} phone number verified."

#     except HTTPException as E:
#         raise E
#     except Exception as E:
#         logging.error(f"Exception error in verify_phone_number: {E}.")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal Server Error: {E}.",
#         )
#     return response


# router.add_api_route(
#     methods=["POST"],
#     path="/phone-number/{verification_id}",
#     endpoint=verify_otp_phone_number,
#     status_code=status.HTTP_200_OK,
#     summary="User phone number verification.",
# )
