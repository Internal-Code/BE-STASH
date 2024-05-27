from loguru import logger
from fastapi import APIRouter
from api.models.response import ResponseGeneral

router = APIRouter(tags=["root"])

async def root():
    logger.info("Endpoint Root.")
    ResponseGeneral.message = "Proceed swagger API Documentation via /api/v1/docs or redoc API Documentation via /api/v1/redoc"
    return ResponseGeneral

router.add_api_route(
    methods=["GET"],
    path="/", 
    response_model=ResponseGeneral,
    endpoint=root
)