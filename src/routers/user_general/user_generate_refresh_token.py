# from typing import Annotated
# from jose import jwt, JWTError
# from datetime import timedelta
# from fastapi import APIRouter, status, Depends
# from src.schema.response import ResponseToken
# from utils.jwt.general import get_current_user
# from utils.database.general import local_time, is_refresh_token_blacklisted
# from src.secret import Config
# from utils.custom_error import (
#     ServiceError,
#     FinanceTrackerApiError,
#     InvalidTokenError,
# )

# config = Config()
# router = APIRouter(tags=["User General"], prefix="/user/general")


# async def refresh_access_token(
#     refresh_token: str, current_user: Annotated[dict, Depends(get_current_user)]
# ) -> ResponseToken:
#     response = ResponseToken()

#     try:
#         blacklisted = await is_refresh_token_blacklisted(refresh_token=refresh_token)

#         if blacklisted is True:
#             raise InvalidTokenError(detail="Refresh token already blacklisted.")

#         payload = jwt.decode(
#             token=refresh_token,
#             key=config.REFRESH_TOKEN_SECRET_KEY,
#             algorithms=[config.ACCESS_TOKEN_ALGORITHM],
#         )
#         user_uuid = payload.get("sub")
#         print(user_uuid)
#         if not user_uuid:
#             raise InvalidTokenError(detail="Invalid refresh token.")

#         access_token_exp = timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED))
#         new_access_token = jwt.encode(
#             {
#                 "sub": user_uuid,
#                 "exp": local_time() + access_token_exp,
#             },
#             key=config.ACCESS_TOKEN_SECRET_KEY,
#             algorithm=config.ACCESS_TOKEN_ALGORITHM,
#         )

#         response.access_token = new_access_token
#         response.token_type = "Bearer"

#     except JWTError:
#         raise InvalidTokenError(detail="Invalid JWT Token.")

#     except FinanceTrackerApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

#     return response


# router.add_api_route(
#     methods=["POST"],
#     path="/refresh-token",
#     response_model=ResponseToken,
#     endpoint=refresh_access_token,
#     status_code=status.HTTP_200_OK,
#     summary="Generate new access token.",
# )
