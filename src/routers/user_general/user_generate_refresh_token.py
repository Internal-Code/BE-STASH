from typing import Annotated
from jose import jwt, JWTError
from datetime import timedelta
from fastapi import APIRouter, status, Depends
from services.postgres.models import BlacklistToken, UserToken
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseToken
from src.schema.request_format import UserRefreshToken
from utils.jwt import get_current_user
from utils.helper import local_time
from utils.query.general import insert_record, find_record
from src.secret import Config
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    InvalidTokenError,
)

config = Config()
router = APIRouter(tags=["User General"], prefix="/user/general")


async def generate_refresh_token_endpoint(
    schema: UserRefreshToken,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseToken:
    response = ResponseToken()
    current_time = local_time()
    user_token_record = await find_record(db=db, table=UserToken, unique_id=current_user.unique_id)
    blacklist_access_token = await find_record(db=db, table=BlacklistToken, access_token=user_token_record.access_token)
    blacklist_refresh_token = await find_record(
        db=db, table=BlacklistToken, refresh_token=user_token_record.refresh_token
    )

    try:
        if blacklist_access_token:
            raise InvalidTokenError(detail="Access token already blacklisted.")

        if blacklist_refresh_token:
            raise InvalidTokenError(detail="Refresh token already blacklisted.")

        payload = jwt.decode(
            token=schema.refresh_token,
            key=config.REFRESH_TOKEN_SECRET_KEY,
            algorithms=[config.ACCESS_TOKEN_ALGORITHM],
        )

        unique_id = payload.get("sub")

        if not unique_id:
            raise InvalidTokenError(detail="Invalid refresh token.")

        access_token_exp = timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED))

        new_access_token = jwt.encode(
            {
                "sub": unique_id,
                "exp": current_time + access_token_exp,
            },
            key=config.ACCESS_TOKEN_SECRET_KEY,
            algorithm=config.ACCESS_TOKEN_ALGORITHM,
        )

        await insert_record(
            db=db, table=UserToken, data={"access_token": new_access_token, "refresh_token": schema.refresh_token}
        )

        response.access_token = new_access_token

    except JWTError:
        raise InvalidTokenError(detail="Invalid JWT Token.")

    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/refresh-token",
    response_model=ResponseToken,
    endpoint=generate_refresh_token_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Generate new access token.",
)
