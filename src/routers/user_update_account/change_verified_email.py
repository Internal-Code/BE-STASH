# from typing import Annotated
# from utils.logger import logging
# from fastapi import APIRouter, status, Depends
# from utils.request_format import AddEmail
# from src.schema.response import ResponseDefault
# from utils.jwt.general import get_current_user
# from utils.custom_error import (
#     EntityForceInputSameDataError,
#     EntityAlreadyExistError,
#     ServiceError,
#     FinanceTrackerApiError,
#     MandatoryInputError,
# )
# from utils.database.general import (
#     is_using_registered_email,
#     update_user_email,
#     extract_data_otp,
#     save_otp_data,
#     local_time,
#     update_otp_data,
# )

# router = APIRouter(tags=["User Update Account"], prefix="/user/update")


# async def change_email_verified_endpoint(
#     schema: AddEmail,
#     current_user: Annotated[dict, Depends(get_current_user)],
# ) -> ResponseDefault:
#     response = ResponseDefault()
#     registered_email = await is_using_registered_email(email=schema.email)
#     initial_data = await extract_data_otp(user_uuid=current_user.user_uuid)

#     try:
#         if not current_user.email:
#             logging.info("User is not input email yet.")
#             raise MandatoryInputError(detail="User should add email first.")

#         if not current_user.verified_email:
#             raise MandatoryInputError(detail="User email should be verified first.")

#         if current_user.email == schema.email:
#             raise EntityForceInputSameDataError(detail="Cannot use same email.")

#         if registered_email:
#             raise EntityAlreadyExistError(detail="Email already taken. Please use another email.")

#         await update_user_email(
#             user_uuid=current_user.user_uuid, email=schema.email, verified_email=False
#         )

#         if initial_data.current_api_hit != 1:
#             logging.info("Re-initialized OTP save data.")
#             await update_otp_data(user_uuid=current_user.user_uuid)

#         if not initial_data:
#             logging.info("Initialized OTP save data.")
#             await save_otp_data(
#                 user_uuid=current_user.user_uuid,
#                 current_api_hit=1,
#                 saved_by_system=True,
#                 save_to_hit_at=local_time(),
#             )

#         response.success = True
#         response.message = "Success update user email."

#     except FinanceTrackerApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

#     return response


# router.add_api_route(
#     methods=["PATCH"],
#     path="/verified-email",
#     endpoint=change_email_verified_endpoint,
#     status_code=status.HTTP_200_OK,
#     response_model=ResponseDefault,
#     summary="Change user email.",
# )
