from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.engine.row import Row
from sqlalchemy import select
from src.auth.routers.dependencies import logging
from src.auth.utils.database.general import local_time
from src.database.connection import database_connection
from src.database.models import user
from src.secret import ACCESS_TOKEN_SECRET_KEY, ACCESS_TOKEN_ALGORITHM

password_content = CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def verify_password(password: str, hashed_password: str) -> str:
    return password_content.verify(password, hashed_password)

async def get_password_hash(password: str) -> str:
    return password_content.hash(password)

async def authenticate_user(username: str, password: str) -> Row | None:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(user).where(user.c.username == username)
                result = await session.execute(query)
                checked = result.fetchone()
                if checked and password_content.verify(password, checked.password):
                    return checked
                else:
                    return None
            except Exception as E:
                logging.error(f"Error during authenticate_user: {E}.")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after authenticate_user: {E}.")
    return None

async def create_access_token(
    username: str, 
    user_id: int, 
    user_uuid: str, 
    expires_delta: timedelta
) -> str:
    encode = {
        'sub': username,
        'id': user_id,
        'user_uuid': user_uuid
    }
    expires = local_time() + expires_delta
    encode.update({'exp': expires})
    encoded_jwt = jwt.encode(
        claims=encode, 
        key=ACCESS_TOKEN_SECRET_KEY, 
        algorithm=ACCESS_TOKEN_ALGORITHM
    )
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict | None:
    try:
        payload = jwt.decode(
            token=token,
            key=ACCESS_TOKEN_SECRET_KEY,
            algorithms=[ACCESS_TOKEN_ALGORITHM]
        )
        username = payload.get('sub')
        user_id = payload.get('id')
        user_uuid = payload.get('user_uuid')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            'username': username,
            'id': user_id,
            'user_uuid': user_uuid
        }
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )