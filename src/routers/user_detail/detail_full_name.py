from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault, FullName
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Detail"], prefix="/user/detail")


async def detail_full_name_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
) -> ResponseDefault:
    logging.info("Detail full name endpoint.")
    response = ResponseDefault()
    full_name_info = FullName()
    try:
        full_name_info.full_name = current_user.full_name
        response.message = "Full name successfully fetched."
        response.data = full_name_info.model_dump()
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
