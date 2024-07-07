from src.auth.routers.dependencies import logging
from fastapi import APIRouter, status
from src.auth.schema.response import ResponseDefault

router = APIRouter(tags=["root"])

async def root() -> ResponseDefault:
    
    logging.info("Endpoint Root.")
    ResponseDefault.message = "Proceed swagger API Documentation via localhost:8000/api/v1/docs or redoc API Documentation via localhost:8000/api/v1/redoc"
    ResponseDefault.success = True
    return ResponseDefault

router.add_api_route(
    methods=["GET"],
    path="/", 
    response_model=ResponseDefault,
    endpoint=root,
    summary="Root endpoint.",
    status_code=status.HTTP_200_OK
)