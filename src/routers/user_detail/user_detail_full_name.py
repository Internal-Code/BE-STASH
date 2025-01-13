from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.custom_error import ServiceError, StashBaseApiError

router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_full_name_endpoint(current_user: Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.message = "Extracted full name info."
        response.data = current_user.full_name
    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/full-name",
    response_model=ResponseDefault,
    endpoint=detail_full_name_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users general information.",
)
