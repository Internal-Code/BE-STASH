from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.utils.request_format import UserInDB
from src.auth.schema.response import ResponseDefault
from src.auth.utils.access_token.security import get_current_active_user

router = APIRouter(tags=["users"], prefix='/users')

async def user(current_user: Annotated[dict, Depends(get_current_active_user)]) -> ResponseDefault:
    response = ResponseDefault()
    
    try:
        response.success=True
        response.message=f"Extracting account {current_user.username}."
        response.data=current_user.to_detail_user().dict()
    except HTTPException as e:
        logging.error(f"Error while extracting current user detail: {e}.")
        raise e
    return response

router.add_api_route(
    methods=["GET"],
    path="/details/{current_user.username}", 
    response_model=ResponseDefault,
    endpoint=user,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated user information."
)