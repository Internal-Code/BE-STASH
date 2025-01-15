from fastapi import APIRouter
from utils.logger import logging
from src.schema.response import ServerStatus

router = APIRouter(tags=["Root"])


async def root() -> ServerStatus:
    logging.info("Endpoint Root.")
    response = ServerStatus()
    response.status = "Server running!"
    return response


router.add_api_route(
    methods=["GET"],
    path="/",
    endpoint=root,
    summary="Health check.",
    response_model=ServerStatus,
)
