from typing import Annotated
from utils.jwt import JWTHandler
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_full_name_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    try:
        response.message = "Extracted full name info."
        response.data = current_user.full_name
    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/full-name",
    response_model=ResponseDefault,
    endpoint=detail_full_name_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated users general information.",
)
