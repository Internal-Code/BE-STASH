from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.jwt.general import get_current_user

router = APIRouter(tags=["users-general"], prefix="/users")


async def user_detail_general_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.success = True
        response.message = f"Extracting account {current_user.full_name} general info."
        response.data = current_user.to_detail_user_general().dict()
    except HTTPException as e:
        logging.error(f"Error while extracting current users general information: {e}.")
        raise e
    return response


router.add_api_route(
    methods=["GET"],
    path="/detail/general",
    response_model=ResponseDefault,
    endpoint=user_detail_general_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users general information.",
)
