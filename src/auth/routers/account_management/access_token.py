from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.routers.dependencies import logging
from src.auth.schema.response import ResponseDefault
from src.secret import ACCESS_TOKEN_EXPIRED
from src.auth.utils.access_token.jwt import authenticate_user, create_access_token


router = APIRouter(
    tags=["account-management"],
    prefix='/auth'
)

async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> ResponseDefault:
    try:
        response = ResponseDefault()
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User could not validated.", 
                headers={"WWW-Authenticate":"Bearer"}
            )
        
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