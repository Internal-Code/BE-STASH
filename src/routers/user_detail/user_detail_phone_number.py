from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.custom_error import ServiceError, StashBaseApiError

router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_phone_number_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.message = "Extracted phone number info."
        response.data = current_user.phone_number
    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
    return response


router.add_api_route(
    methods=["GET"],
    path="/phone-number",
    response_model=ResponseDefault,
    endpoint=detail_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users phone number information.",
)
