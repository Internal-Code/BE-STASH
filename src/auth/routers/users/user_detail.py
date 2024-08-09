from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.jwt.security import get_current_user

router = APIRouter(tags=["users"], prefix="/users")


async def users(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.success = True
        response.message = f"Extracting account {current_user.username}."
        response.data = current_user.to_detail_user().dict()
    except HTTPException as e:
        logging.error(f"Error while extracting current users detail: {e}.")
        raise e
    return response


router.add_api_route(
    methods=["GET"],
    path="/detail",
    response_model=ResponseDefault,
    endpoint=users,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users information.",
)
