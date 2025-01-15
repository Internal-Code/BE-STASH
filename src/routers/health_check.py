from fastapi import APIRouter
from utils.logger import logging
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Root"])


async def root():
    logging.info("Endpoint Root.")
    return JSONResponse(content={"status": "Server running!"})


router.add_api_route(
    methods=["GET"],
    path="/",
    endpoint=root,
    summary="Health check."
)