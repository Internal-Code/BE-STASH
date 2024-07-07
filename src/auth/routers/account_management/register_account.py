from src.auth.routers.dependencies import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import CreateUser
from src.auth.utils.database.general import filter_registered_user, register_account_format, local_time
from src.database.connection import database_connection
from src.database.models import user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.secret import ACCESS_TOKEN_SECRET_KEY, ACCESS_TOKEN_ALGORITHM, ACCESS_TOKEN_EXPIRED, ACCESS_TOKEN_REFRESH_KEY
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated

password_content = CryptContext(schemes=['bcrypt'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(
    tags=["account-management"],
    prefix='/auth'
)

async def verify_password(password: str, hashed_password: str) -> str:
    return password_content.verify(password, hashed_password)

async def get_password_hash(password: str) -> str:
    return password_content.hash(password)


async def register_user(schema: CreateUser) -> ResponseDefault:
    
    """
        Create a schema with all the information:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
        - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
        - **budget**: This specifies the planned amount of money allocated for the category within the specified month and year. The budget represents your spending limit for that particular category during that time frame.
    """
    
    response = ResponseDefault()
    try:
        is_available = await filter_registered_user(
            username=schema.username,
            email=schema.email,
        )
        if is_available:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account with username: {schema.username} or email: {schema.email} already registered. Please create an another account")
        
        prepared_data = register_account_format(
            first_name=schema.first_name,
            last_name=schema.last_name,
            username=schema.username,
            email=schema.email,
            password=await get_password_hash(schema.password),
            is_disabled=schema.is_disabled
        )

        logging.info("Endpoint register account.")
        async with database_connection().connect() as session:
            try:
                query = user.insert().values(prepared_data)
                await session.execute(query)
                await session.commit()
                logging.info(f"Created new account.")
            except Exception as E:
                logging.error(f"Error while creating account: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during transaction: {E}.")
            finally:
                await session.close()
        
        response.message = "Register account success."
        response.success = True
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    return response

router.add_api_route(
    methods=["POST"],
    path="/register", 
    response_model=ResponseDefault,
    endpoint=register_user,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budgeting schema for each month."
)