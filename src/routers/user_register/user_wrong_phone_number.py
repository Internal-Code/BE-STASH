# from fastapi import APIRouter, status
# from utils.logger import logging
# from utils.jwt.general import get_user
# from src.schema.response import ResponseDefault, UniqueId
# from utils.validator import check_uuid, check_phone_number
# from utils.request_format import ChangeUserPhoneNumber
# from utils.custom_error import (
#     EntityForceInputSameDataError,
#     EntityAlreadyExistError,
#     ServiceError,
#     StashBaseApiError,
#     MandatoryInputError,
#     EntityDoesNotExistError,
#     EntityAlreadyFilledError,
# )
# from utils.database.general import (
#     update_user_phone_number,
#     update_otp_data,
# )

# router = APIRouter(tags=["User Register"], prefix="/user/register")


# async def wrong_phone_number_endpoint(
#     schema: ChangeUserPhoneNumber, unique_id: str
# ) -> ResponseDefault:
#     response = ResponseDefault()
#     check_uuid(unique_id=unique_id)
#     await check_phone_number(phone_number=schema.phone_number)
#     try:
#         account = await get_user(unique_id=unique_id)
#         registered_phone_number = await get_user(phone_number=schema.phone_number)

#         if account.phone_number == schema.phone_number:
#             raise EntityForceInputSameDataError(
#                 detail="Cannot changed into same phone number.",
#             )

#         if registered_phone_number:
#             raise EntityAlreadyExistError(detail="Phone number already registered.")

#         if not account.full_name:
#             raise MandatoryInputError(
#                 detail="User should fill full name first.",
#             )

#         if not account:
#             raise EntityDoesNotExistError(detail="Account not found.")

#         if account.pin:
#             raise EntityAlreadyFilledError(detail="Account already set pin.")

#         if account:
#             logging.info("Update registered phone number.")
#             await update_user_phone_number(user_uuid=unique_id, phone_number=schema.phone_number)
#             logging.info("Re-initialized OTP save data.")
#             await update_otp_data(user_uuid=unique_id)

#             response.success = True
#             response.message = "Phone number successfully updated."
#             response.data = UniqueId(unique_id=account.user_uuid)
#     except StashBaseApiError as FTE:
#         raise FTE
#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
#     return response


# router.add_api_route(
#     methods=["PATCH"],
#     path="/wrong-phone-number/{unique_id}",
#     response_model=ResponseDefault,
#     endpoint=wrong_phone_number_endpoint,
#     status_code=status.HTTP_202_ACCEPTED,
#     summary="Wrong registered account phone number.",
# )
