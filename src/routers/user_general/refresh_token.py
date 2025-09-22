from typing import Annotated
from jose import jwt, JWTError
from datetime import timedelta
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.time_utils import local_time
from utils.query import QueryDatabase
from src.schema.response import ResponseToken
from fastapi import APIRouter, status, Depends
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.model import BlacklistToken, UserToken
from src.schema.request_format import RefreshTokenPayload
from src.secret import Config
from utils.error import (
    ServiceError,
    StashBaseApiError,
    InvalidTokenError,
)

config = Config()
jwt_handler = JWTHandler()
router = APIRouter(tags=["User General"], prefix="/user/general")


async def generate_refresh_token_endpoint(
    schema: RefreshTokenPayload,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseToken:
    logging.info("Refresh token endpoint.")
    response = ResponseToken()
    query = QueryDatabase(db)
    current_time = local_time()

    try:
        user_token_record = await query.find(
            table=UserToken, unique_id=current_user.unique_id
        )

        blacklist_access_token = await query.find(
            table=BlacklistToken, access_token=user_token_record.access_token
        )

        if blacklist_access_token:
            logging.error("Access token already blacklisted.")
            raise InvalidTokenError(detail="Access token already blacklisted.")

        blacklist_refresh_token = await query.find(
            table=BlacklistToken, refresh_token=user_token_record.refresh_token
        )

        if blacklist_refresh_token:
            logging.error("Refresh token already blacklisted.")
            raise InvalidTokenError(detail="Refresh token already blacklisted.")

        logging.info("Decoding refresh token.")
        payload = jwt.decode(
            token=schema.refresh_token,
            key=config.REFRESH_TOKEN_SECRET_KEY,
            algorithms=[config.ACCESS_TOKEN_ALGORITHM],
        )

        unique_id = payload.get("sub")

        if not unique_id:
            logging.error("Invalid refresh token.")
            raise InvalidTokenError(detail="Invalid refresh token.")

        access_token_exp = timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED))

        logging.info("Generating new access token.")
        new_access_token = jwt.encode(
            {
                "sub": unique_id,
                "exp": current_time + access_token_exp,
            },
            key=config.ACCESS_TOKEN_SECRET_KEY,
            algorithm=config.ACCESS_TOKEN_ALGORITHM,
        )

        await query.insert(
            table=UserToken,
            data={
                "unique_id": unique_id,
                "access_token": new_access_token,
                "refresh_token": schema.refresh_token,
            },
        )

        response.access_token = new_access_token

    except JWTError:
        raise InvalidTokenError(detail="Invalid refresh token.")

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/refresh-token",
    response_model=ResponseToken,
    endpoint=generate_refresh_token_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Generate new access token.",
)
