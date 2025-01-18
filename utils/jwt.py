from typing import Annotated
from datetime import timedelta
from jose import JWTError, jwt
from sqlalchemy.engine.row import Row
from passlib.context import CryptContext
from utils.logger import logging
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from services.postgres.connection import get_db
from src.schema.validator import SecurityCodeValidator, UniqueIdValidator
from src.secret import Config
from utils.helper import local_time
from services.postgres.models import User, BlacklistToken
from utils.query.general import find_record
from utils.custom_error import AuthenticationFailed, DataNotFoundError


config = Config()
password_content = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/general/login")


def verify_pin(pin: str, hashed_pin: str) -> str:
    return password_content.verify(pin, hashed_pin)


def get_password_hash(password: str) -> str:
    return password_content.hash(password)


async def authenticate_user(unique_id: str, pin: str) -> Row | None:
    validated_uuid = UniqueIdValidator.validate_uuid(unique_id=unique_id)
    validated_pin = SecurityCodeValidator.validate_security_code(type="pin", value=pin)

    async for db in get_db():
        account_record = await find_record(db=db, table=User, unique_id=validated_uuid)

    if not account_record:
        raise DataNotFoundError(detail="User not found.")
    if not account_record.pin:
        raise AuthenticationFailed(detail="User has not set pin.")
    if not verify_pin(pin=validated_pin, hashed_pin=account_record.pin):
        raise AuthenticationFailed(detail="invalid pin.")

    return account_record


def create_access_token(data: dict, access_token_expires: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + access_token_expires
    to_encode.update({"exp": expires})
    encoded_access_token = jwt.encode(
        claims=to_encode, key=config.ACCESS_TOKEN_SECRET_KEY
    )
    return encoded_access_token


def create_refresh_token(data: dict, refresh_token_expires: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + refresh_token_expires
    to_encode.update({"exp": expires})
    encoded_refresh_token = jwt.encode(
        claims=to_encode, key=config.REFRESH_TOKEN_SECRET_KEY
    )
    return encoded_refresh_token


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> Row | None:
    async for db in get_db():
        blacklisted_record = await find_record(
            db=db, table=BlacklistToken, access_token=token
        )

    try:
        if blacklisted_record:
            raise AuthenticationFailed(
                detail="Session expired. Please perform re-login."
            )

        payload = jwt.decode(
            token=token,
            key=config.ACCESS_TOKEN_SECRET_KEY,
            algorithms=[config.ACCESS_TOKEN_ALGORITHM],
        )

        user_uuid = payload.get("sub")

        async for db in get_db():
            users = await find_record(db=db, table=User, unique_id=user_uuid)

        if not user_uuid:
            raise AuthenticationFailed(detail="Could not validate credentials.")

    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise AuthenticationFailed(detail="Could not validate credentials.", name="JWT")
    return users
