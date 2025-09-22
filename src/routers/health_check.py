from fastapi import APIRouter, status
from utils.logger import logging
from src.schema.response import BaseResponse

router = APIRouter(tags=["Root"])


async def health_check_endpoint() -> BaseResponse:
    logging.info("Health check endpoint.")
    return BaseResponse(message="Server running!")


router.add_api_route(
    methods=["GET"],
    path="/",
    endpoint=health_check_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Health check.",
    response_model=BaseResponse,
)
