from fastapi import APIRouter
from utils.logger import logging
from src.schema.response import ServerStatus

router = APIRouter(tags=["health_check_endpoint"])


async def health_check_endpoint() -> ServerStatus:
    logging.info("Endpoint health_check_endpoint.")
    response = ServerStatus()
    response.status = "Server running!"
    return response


router.add_api_route(
    methods=["GET"],
    path="/",
    endpoint=health_check_endpoint,
    summary="Health check.",
    response_model=ServerStatus,
)
