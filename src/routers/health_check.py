from fastapi import APIRouter, status
from utils.logger import logging
from src.schema.response import ResponseDefault

router = APIRouter(tags=["Root"])


async def health_check_endpoint() -> ResponseDefault:
    logging.info("Health check endpoint.")
    response = ResponseDefault()
    response.message = "Server running!"
    return response


router.add_api_route(
    methods=["GET"],
    path="/",
    endpoint=health_check_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Health check.",
    response_model=ResponseDefault,
)
