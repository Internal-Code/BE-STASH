# from typing import Annotated
# from utils.logger import logging
# from fastapi import APIRouter, status, Depends
# from services.postgres.models import blacklist_tokens
# from src.schema.response import ResponseDefault
# from utils.jwt.general import get_current_user
# from services.postgres.connection import database_connection
# from utils.database.general import (
#     local_time,
#     is_refresh_token_blacklisted,
#     is_access_token_blacklisted,
#     extract_tokens,
# )
# from utils.custom_error import (
#     ServiceError,
#     DatabaseError,
#     FinanceTrackerApiError,
#     InvalidTokenError,
# )

# router = APIRouter(tags=["User General"], prefix="/user/general")


# async def user_logout(
#     current_user: Annotated[dict, Depends(get_current_user)],
# ) -> ResponseDefault:
#     response = ResponseDefault()
#     try:
#         token_data = await extract_tokens(user_uuid=current_user.user_uuid)

#         validate_refresh_token = await is_refresh_token_blacklisted(
#             refresh_token=token_data.refresh_token
#         )
#         validate_access_token = await is_access_token_blacklisted(
#             access_token=token_data.access_token
#         )

#         if validate_refresh_token is True or validate_access_token is True:
#             raise InvalidTokenError(detail="Token already blacklisted.")

#         async with database_connection().connect() as session:
#             try:
#                 query = blacklist_tokens.insert().values(
#                     blacklisted_at=local_time(),
#                     user_uuid=current_user.user_uuid,
#                     access_token=token_data.access_token,
#                     refresh_token=token_data.refresh_token,
#                 )
#                 await session.execute(query)
#                 await session.commit()
#                 logging.info(f"User {current_user.full_name} logged out successfully.")
#                 response.message = "Logout successful."
#                 response.success = True
#             except Exception as E:
#                 logging.error(f"Error during logout: {E}.")
#                 await session.rollback()
#                 raise DatabaseError(
#                     detail=f"Database error: {E}.",
#                 )
#             finally:
#                 await session.close()
#     except FinanceTrackerApiError as FTE:
#         raise FTE
#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
#     return response


# router.add_api_route(
#     methods=["POST"],
#     path="/logout",
#     response_model=ResponseDefault,
#     endpoint=user_logout,
#     status_code=status.HTTP_200_OK,
#     summary="Logout logged in current user.",
# )
