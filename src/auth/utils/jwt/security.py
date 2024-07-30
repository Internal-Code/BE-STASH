from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.engine.row import Row
from sqlalchemy import select
from src.auth.utils.logging import logging
from src.auth.utils.database.general import local_time, is_access_token_blacklisted
from src.database.connection import database_connection
from src.database.models import users
from src.auth.utils.request_format import TokenData, UserInDB, DetailUser
from src.secret import (
    ACCESS_TOKEN_SECRET_KEY,
    ACCESS_TOKEN_ALGORITHM,
    REFRESH_TOKEN_SECRET_KEY,
)

password_content = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def verify_password(password: str, hashed_password: str) -> str:
    return password_content.verify(password, hashed_password)


async def get_password_hash(password: str) -> str:
    return password_content.hash(password)


async def get_user(username: str) -> UserInDB | None:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(users).where(users.c.username == username)
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    logging.info(f"User {checked.username} found.")
                    user_data = UserInDB(
                        user_uuid=checked.user_uuid,
                        created_at=checked.created_at,
                        updated_at=checked.updated_at,
                        first_name=checked.first_name,
                        last_name=checked.last_name,
                        username=checked.username,
                        email=checked.email,
                        phone_number=checked.phone_number,
                        password=checked.password,
                        verified_email=checked.verified_email,
                        verified_phone_number=checked.verified_phone_number,
                    )
                    return user_data
                else:
                    logging.error(f"User {username} not found.")
                    return None
            except Exception as E:
                logging.error(f"Error during get_user: {E}.")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after get_user: {E}.")
    return None


async def authenticate_user(username: str, password: str) -> Row | None:
    try:
        users = await get_user(username=username)
        if not users:
            logging.error(f"Authentication failed: users {username} not found.")
            return None
        if not await verify_password(password=password, hashed_password=users.password):
            logging.error(
                f"Authentication failed: invalid password for users {username}."
            )
            return None
    except Exception as E:
        logging.error(f"Error after authenticate_user: {E}.")
        return None
    return users


async def create_access_token(data: dict, access_token_expires: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + access_token_expires
    to_encode.update({"exp": expires})
    encoded_access_token = jwt.encode(claims=to_encode, key=ACCESS_TOKEN_SECRET_KEY)
    return encoded_access_token


async def create_refresh_token(data: dict, refresh_token_expires: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + refresh_token_expires
    to_encode.update({"exp": expires})
    encoded_refresh_token = jwt.encode(claims=to_encode, key=REFRESH_TOKEN_SECRET_KEY)
    return encoded_refresh_token


async def get_access_token(access_token: str = Depends(oauth2_scheme)) -> str:
    return access_token


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> DetailUser | None:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    blacklisted_access_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired. Please perform re login.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        validate_access_token = await is_access_token_blacklisted(access_token=token)

        if validate_access_token is True:
            raise blacklisted_access_token

        payload = jwt.decode(
            token=token,
            key=ACCESS_TOKEN_SECRET_KEY,
            algorithms=[ACCESS_TOKEN_ALGORITHM],
        )

        username = payload.get("sub")
        token_data = TokenData(username=username)
        users = await get_user(username=token_data.username)

        if username is None or users is None:
            raise credentials_exception
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise credentials_exception
    return users
