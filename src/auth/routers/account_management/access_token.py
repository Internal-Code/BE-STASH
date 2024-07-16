from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.database.connection import database_connection
from src.auth.utils.database.general import local_time
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseToken
from src.secret import ACCESS_TOKEN_EXPIRED
from src.auth.utils.access_token.security import authenticate_user, create_access_token
from src.auth.utils.database.general import update_latest_login

router = APIRouter(
    tags=["account-management"],
    prefix='/auth'
)

async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> ResponseToken:
    try:
        response = ResponseToken()
        user_in_db = await authenticate_user(form_data.username, form_data.password)
        if not user_in_db:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User could not be validated.", 
                headers={"WWW-Authenticate":"Bearer"}
            )

        latest_login = await update_latest_login(username=user_in_db.username, email=user_in_db.email)
        if latest_login is True:
            token = await create_access_token(
                data={
                    "sub": user_in_db.username, 
                    "user_id": user_in_db.id, 
                    "user_uuid": str(user_in_db.user_uuid)
                },
                expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED))
            )
            response.access_token = token
            response.token_type = 'bearer'
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
    endpoint=login_for_access_token,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Authenticate user and return access token."
)