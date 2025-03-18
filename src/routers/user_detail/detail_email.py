from typing import Annotated
from utils.jwt import JWTHandler
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault, DetailEmailResponse
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_email_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    email_info = DetailEmailResponse()
    try:
        email_info.email = current_user.email
        email_info.is_email_verified = current_user.verified_email
        response.message = "Extracted email info."
        response.data = email_info.model_dump()
    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/email",
    response_model=ResponseDefault,
    endpoint=detail_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users email information.",
)
