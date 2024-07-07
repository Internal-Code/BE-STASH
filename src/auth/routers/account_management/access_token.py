from datetime import timedelta
from sqlalchemy import select
from src.auth.routers.dependencies import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.schema.response import ResponseDefault
from src.auth.utils.database.general import local_time
from src.database.connection import database_connection
from src.database.models import user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.engine.row import Row
from src.secret import ACCESS_TOKEN_SECRET_KEY, ACCESS_TOKEN_ALGORITHM, ACCESS_TOKEN_EXPIRED
from jose import JWTError
from passlib.context import CryptContext
from typing import Annotated

password_content = CryptContext(schemes=['bcrypt'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
router = APIRouter(
    tags=["account-management"],
    prefix='/auth'
)

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
    expires_delta: timedelta
) -> str:
    encode = {
        'sub': username,
        'id': user_id,
    }
    expires = (local_time() + expires_delta).timestamp()
    encode.update({'exp': expires})
    return jwt.encode(
        claims=encode, 
        key=ACCESS_TOKEN_SECRET_KEY, 
        algorithm=ACCESS_TOKEN_ALGORITHM
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict | None:
    try:
        payload = jwt.decode(
            token=token,
            key=ACCESS_TOKEN_SECRET_KEY,
            algorithms=[ACCESS_TOKEN_ALGORITHM]
        )
        logging.info(f"Payload received: {payload}")
        username = payload.get('sub')
        user_id = payload.get('id')
        if username is None or id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User could not validated.")
        return {
            'username':username,
            'id': user_id
        }
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User could not validated.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User could not be validated.")

async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> ResponseDefault:
    try:
        response = ResponseDefault()
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User could not validated.")
        
        token = await create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED)))
        response.success=True
        response.message='User authenticated'
        response.data={
            'access_token':token,
            'token_type':'Bearer'
        }
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    return response


router.add_api_route(
    methods=["POST"],
    path="/token", 
    response_model=ResponseDefault,
    endpoint=login,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a budgeting schema for each month."
)