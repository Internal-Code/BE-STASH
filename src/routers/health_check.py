from utils.logger import logging
from fastapi import APIRouter, status
from src.schema.response import ResponseDefault

router = APIRouter(tags=["Root"])


async def root() -> ResponseDefault:
    logging.info("Endpoint Root.")
    response = ResponseDefault()
    response.message = "Server running!"
    return response


router.add_api_route(
    methods=["GET"],
    path="/",
    endpoint=root,
    summary="Health check.",
    status_code=status.HTTP_200_OK,
    response_model=ResponseDefault,
)
