from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import EmailStr
from sqlalchemy.engine.row import Row
from sqlalchemy import select
from sqlalchemy.sql import and_
from src.auth.utils.logging import logging
from src.auth.utils.database.general import local_time
from src.database.connection import database_connection
from src.database.models import user
from src.secret import ACCESS_TOKEN_SECRET_KEY, ACCESS_TOKEN_ALGORITHM
from src.auth.utils.request_format import TokenData, UserInDB

password_content = CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def verify_password(password: str, hashed_password: str) -> str:
    return password_content.verify(password, hashed_password)

async def get_password_hash(password: str) -> str:
    return password_content.hash(password)

async def get_user(username: str) -> UserInDB | None:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(user).where(user.c.username == username)
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    logging.info(f"User {username} found.")
                    user_data = UserInDB(
                        user_uuid=checked.user_uuid,
                        id=checked.id,
                        first_name=checked.first_name,
                        last_name=checked.last_name,
                        username=checked.username,
                        email=checked.email,
                        password=checked.password,
                        is_deactivated=checked.is_deactivated
                    )
                    return user_data
                else:
                    logging.error(f"User {username} not found.")
                    return None
            except Exception as E:
                logging.error(f"Error during authenticate_user: {E}.")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after authenticate_user: {E}.")
    return None


async def authenticate_user(username: str, password: str) -> Row | None:
    try:
        user = await get_user(username=username)
        if not user:
            return None
        if not await verify_password(password, user.password):
            return None
    except Exception as E:
        logging.error(f"Error after authenticate_user: {E}.")
        return None
    return user

async def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expires = local_time() + expires_delta
    to_encode.update({'exp': expires})
    encoded_jwt = jwt.encode(
        claims=to_encode, 
        key=ACCESS_TOKEN_SECRET_KEY, 
        algorithm=ACCESS_TOKEN_ALGORITHM
    )
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB | None:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token=token,
            key=ACCESS_TOKEN_SECRET_KEY,
            algorithms=[ACCESS_TOKEN_ALGORITHM]
        )
        username = payload.get('sub')
        token_data = TokenData(username=username)
        user = await get_user(username=token_data.username)
        if username is None or user is None:
            raise credentials_exception
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[str, Depends(get_current_user)]) -> str | dict:
    if current_user.is_deactivated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user