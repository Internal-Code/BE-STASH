# from typing import Annotated
# from utils.logger import logging
# from fastapi import APIRouter, status, Depends
# from utils.request_format import AddEmail
# from src.schema.response import ResponseDefault
# from utils.jwt.general import get_current_user
# from utils.custom_error import (
#     EntityAlreadyVerifiedError,
#     EntityAlreadyExistError,
#     EntityAlreadyAddedError,
#     EntityForceInputSameDataError,
#     ServiceError,
#     StashBaseApiError,
# )
# from utils.database.general import (
#     is_using_registered_email,
#     update_user_email,
#     extract_data_otp,
#     save_otp_data,
#     local_time,
# )

# router = APIRouter(tags=["User Detail"], prefix="/user/detail")


# async def add_email_endpoint(
#     schema: AddEmail,
#     current_user: Annotated[dict, Depends(get_current_user)],
# ) -> ResponseDefault:
#     response = ResponseDefault()
#     registered_email = await is_using_registered_email(email=schema.email)
#     initial_data = await extract_data_otp(user_uuid=current_user.user_uuid)

#     try:
#         if registered_email:
#             raise EntityAlreadyExistError(detail="Email already taken. Please use another email.")

#         if current_user.verified_email:
#             raise EntityAlreadyVerifiedError(detail="User already have an verified email.")

#         if current_user.email:
#             raise EntityAlreadyAddedError(detail="User already have an email.")

#         if current_user.email == schema.email:
#             raise EntityForceInputSameDataError(detail="Cannot use same email.")

#         await update_user_email(
#             user_uuid=current_user.user_uuid, email=schema.email, verified_email=False
#         )

#         if not initial_data:
#             logging.info("Initialized OTP save data.")
#             await save_otp_data(
#                 user_uuid=current_user.user_uuid,
#                 current_api_hit=1,
#                 saved_by_system=True,
#                 save_to_hit_at=local_time(),
#             )

#         response.success = True
#         response.message = "Success add new email."

#     except StashBaseApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

#     return response


# router.add_api_route(
#     methods=["PATCH"],
#     path="/add-email",
#     response_model=ResponseDefault,
#     endpoint=add_email_endpoint,
#     status_code=status.HTTP_201_CREATED,
#     summary="User add new email.",
# )
