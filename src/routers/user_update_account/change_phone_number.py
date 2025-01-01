# from typing import Annotated
# from utils.logger import logging
# from fastapi import APIRouter, status, Depends
# from utils.jwt.general import get_current_user
# from utils.validator import check_phone_number
# from src.schema.response import ResponseDefault, UniqueID
# from utils.request_format import ChangeUserPhoneNumber
# from utils.custom_error import (
#     EntityForceInputSameDataError,
#     EntityAlreadyExistError,
#     ServiceError,
#     StashBaseApiError,
# )
# from utils.database.general import (
#     local_time,
#     is_using_registered_phone_number,
#     update_user_phone_number,
#     save_otp_data,
#     extract_data_otp,
# )

# router = APIRouter(tags=["User Update Account"], prefix="/user/update")


# async def change_phone_number_endpoint(
#     schema: ChangeUserPhoneNumber,
#     current_user: Annotated[dict, Depends(get_current_user)],
# ) -> ResponseDefault:
#     response = ResponseDefault()

#     validated_phone_number = await check_phone_number(phone_number=schema.phone_number)
#     registered_phone_number = await is_using_registered_phone_number(
#         phone_number=validated_phone_number
#     )
#     initial_data = await extract_data_otp(user_uuid=current_user.user_uuid)

#     try:
#         if validated_phone_number == current_user.phone_number:
#             raise EntityForceInputSameDataError(detail="Cannot use same phone number.")

#         if registered_phone_number:
#             raise EntityAlreadyExistError(
#                 detail="Phone number already used.",
#             )

#         logging.info("Updating user phone number.")
#         await update_user_phone_number(
#             user_uuid=current_user.user_uuid, phone_number=validated_phone_number
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
#         response.message = "Update phone number success."
#         response.data = UniqueID(unique_id=current_user.user_uuid)

#     except StashBaseApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

#     return response


# router.add_api_route(
#     methods=["PATCH"],
#     path="/phone-number",
#     endpoint=change_phone_number_endpoint,
#     status_code=status.HTTP_200_OK,
#     summary="Change user phone number.",
# )
