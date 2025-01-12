from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.custom_error import ServiceError, StashBaseApiError

router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_email_endpoint(current_user: Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.message = "Extracted email info."
        response.data = current_user.email
    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/email",
    response_model=ResponseDefault,
    endpoint=detail_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users email information.",
)
