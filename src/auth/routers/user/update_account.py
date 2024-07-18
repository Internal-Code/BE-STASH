from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.utils.request_format import UserInDB
from src.auth.utils.access_token.security import get_current_active_user

router = APIRouter(tags=["user"], prefix='/user')

async def user(current_user: Annotated[UserInDB, Depends(get_current_active_user)]) -> UserInDB:
    try:
        return current_user
    except HTTPException as e:
        logging.error(f"Error while creating category: {e}.")
        raise e

router.add_api_route(
    methods=["POST"],
    path="/update/{current_user.username}", 
    response_model=UserInDB,
    endpoint=user,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated user information."
)