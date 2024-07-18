from jose import jwt, JWTError
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from src.auth.schema.response import ResponseToken
from src.auth.utils.database.general import local_time
from src.auth.utils.logging import logging
from src.secret import (
    REFRESH_TOKEN_SECRET_KEY, 
    ACCESS_TOKEN_SECRET_KEY, 
    ACCESS_TOKEN_ALGORITHM, 
    ACCESS_TOKEN_EXPIRED
)

router = APIRouter(tags=["auth"], prefix='/auth')

async def refresh_access_token(refresh_token: str) -> ResponseToken:
    
    invalid_refresh_token = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    try:
        payload = jwt.decode(refresh_token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM])
        username = payload.get("sub")
        user_uuid = payload.get("user_uuid")
        if user_uuid is None or username is None:
            raise invalid_refresh_token

        access_token_exp = timedelta(minutes=int(ACCESS_TOKEN_EXPIRED))
        new_access_token = jwt.encode(
            {
                "sub": username, 
                "user_uuid": user_uuid,
                "exp": local_time() + access_token_exp
            }, 
            key=ACCESS_TOKEN_SECRET_KEY, 
            algorithm=ACCESS_TOKEN_ALGORITHM
        )
        
        return ResponseToken(access_token=new_access_token, token_type="Bearer")
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise invalid_refresh_token

router.add_api_route(
    methods=["POST"],
    path="/refresh-token",
    response_model=ResponseToken,
    endpoint=refresh_access_token,
    status_code=status.HTTP_200_OK,
    summary="Generate new access token."
)
