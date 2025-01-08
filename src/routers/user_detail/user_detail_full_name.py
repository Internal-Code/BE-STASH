from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.custom_error import ServiceError, StashBaseApiError

router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def user_detail_general_endpoint(current_user: Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.success = True
        response.message = "Extracted full name info."
        response.data = current_user.full_name
    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
    return response


router.add_api_route(
    methods=["GET"],
    path="/full-name",
    response_model=ResponseDefault,
    endpoint=user_detail_general_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users general information.",
)
