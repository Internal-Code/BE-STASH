from typing import Annotated
from utils.jwt import JWTHandler
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault, PhoneNumber
from utils.error import ServiceError, StashBaseApiError


jwt_handler = JWTHandler()
router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_phone_number_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    phone_number_info = PhoneNumber()
    try:
        phone_number_info.phone_number = current_user.phone_number
        response.message = "Extracted phone number info."
        response.data = phone_number_info.model_dump()
    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/phone-number",
    response_model=ResponseDefault,
    endpoint=detail_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users phone number information.",
)
