from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.routers.dependencies import logging
from src.auth.schema.response import ResponseToken
from src.secret import ACCESS_TOKEN_EXPIRED
from src.auth.utils.access_token.jwt import authenticate_user, create_access_token

router = APIRouter(
    tags=["account-management"],
    prefix='/auth'
)

async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> ResponseToken:
    try:
        response = ResponseToken()
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User could not be validated.", 
                headers={"WWW-Authenticate":"Bearer"}
            )
        
        token = await create_access_token(
            username=user.username, 
            user_id=user.id, 
            expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED))
        )
        response.access_token=token
        response.token_type='bearer'
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error while creating category: {e}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}.")
    return response

router.add_api_route(
    methods=["POST"],
    path="/token", 
    response_model=ResponseToken,
    endpoint=login,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Authenticate user and return access token."
)