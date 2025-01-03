from typing import Annotated
from pydantic import EmailStr
from datetime import timedelta
from jose import JWTError, jwt
from sqlalchemy import and_, select
from sqlalchemy.engine.row import Row
from passlib.context import CryptContext
from utils.logger import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from services.postgres.connection import database_connection, get_db
from utils.validator import check_security_code, check_uuid
from src.secret import Config
from utils.helper import local_time
from services.postgres.models import User, BlacklistToken
from utils.query.general import find_record
from utils.custom_error import AuthenticationFailed, EntityDoesNotExistError
from src.schema.request_format import (
    UserInDB,
)

config = Config()
password_content = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/general/login")


def verify_pin(pin: str, hashed_pin: str) -> str:
    return password_content.verify(pin, hashed_pin)


def get_password_hash(password: str) -> str:
    return password_content.hash(password)


async def get_user(phone_number: str = None, unique_id: str = None, email: EmailStr = None) -> UserInDB | None:
    try:
        async with database_connection().connect() as session:
            try:
                filters = []

                if phone_number:
                    filters.append(User.c.phone_number == phone_number)
                if unique_id:
                    filters.append(User.c.user_uuid == unique_id)
                if email:
                    filters.append(User.c.email == email)

                if not filters:
                    logging.error("No valid filter provided.")

                query = select(User).where(and_(*filters))
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    logging.info("User found.")
                    user_data = UserInDB(
                        user_uuid=str(checked.user_uuid),
                        created_at=checked.created_at,
                        updated_at=checked.updated_at,
                        full_name=checked.full_name,
                        email=checked.email,
                        phone_number=checked.phone_number,
                        pin=checked.pin,
                        verified_email=checked.verified_email,
                        verified_phone_number=checked.verified_phone_number,
                    )
                    return user_data

                logging.warning("User not found.")
            except Exception as E:
                logging.error(f"Error during get_user: {E}.")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after get_user: {E}.")
    return None


async def authenticate_user(unique_id: str, pin: str) -> Row | None:
    validated_uuid = check_uuid(unique_id=unique_id)
    validated_pin = check_security_code(type="pin", value=pin)

    async for db in get_db():
        account_record = await find_record(db=db, table=User, unique_id=validated_uuid)
        break

    if not account_record:
        raise EntityDoesNotExistError(detail="User not found.")
    if not account_record.pin:
        raise AuthenticationFailed(detail="User has not set pin.")
    if not verify_pin(pin=validated_pin, hashed_pin=account_record.pin):
        raise AuthenticationFailed(detail="invalid pin.")

    return account_record


def create_access_token(data: dict, access_token_expires: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + access_token_expires
    to_encode.update({"exp": expires})
    encoded_access_token = jwt.encode(claims=to_encode, key=config.ACCESS_TOKEN_SECRET_KEY)
    return encoded_access_token


def create_refresh_token(data: dict, refresh_token_expires: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + refresh_token_expires
    to_encode.update({"exp": expires})
    encoded_refresh_token = jwt.encode(claims=to_encode, key=config.REFRESH_TOKEN_SECRET_KEY)
    return encoded_refresh_token


async def get_access_token(access_token: str = Depends(oauth2_scheme)) -> str:
    return access_token


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> Row | None:
    async for db in get_db():
        break

    blacklisted_record = await find_record(db=db, table=BlacklistToken, access_token=token)

    try:
        if blacklisted_record:
            logging.error("Access token is blacklisted.")
            raise AuthenticationFailed(detail="Session expired. Please perform re login.")

        payload = jwt.decode(
            token=token,
            key=config.ACCESS_TOKEN_SECRET_KEY,
            algorithms=[config.ACCESS_TOKEN_ALGORITHM],
        )

        user_uuid = payload.get("sub")

        async for db in get_db():
            break

        users = await find_record(db=db, table=User, unique_id=user_uuid)

        if not user_uuid:
            raise AuthenticationFailed(detail="Could not validate credentials.")

    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise AuthenticationFailed(detail="Could not validate credentials.", name="JWT")
    return users


async def verify_email_status(token: Annotated[str, Depends(oauth2_scheme)]) -> bool:
    already_verified = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User email already verified.",
    )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "bearer"},
    )

    try:
        # payload = jwt.decode(
        #     token=token,
        #     key=config.ACCESS_TOKEN_SECRET_KEY,
        #     algorithms=[config.ACCESS_TOKEN_ALGORITHM],
        # )

        # user_uuid = payload.get("sub")

        # token_data = TokenData(user_uuid=user_uuid)
        # users = await get_user(unique_id=token_data.user_uuid)
        email_status = User.verified_email

        if email_status:
            raise already_verified
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise credentials_exception
    return email_status
