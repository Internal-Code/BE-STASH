from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.query import QueryDatabase
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import MonthlySchema
from src.schema.response import ResponseDefault
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def list_schema_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("List schema endopoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)

    try:
        entries = await query.find(
            table=MonthlySchema,
            fetch="all",
            unique_id=current_user.unique_id,
            deleted_at=None,
        )
        if not entries:
            logging.warning("User is not created schema.")
            response.message = "User is not created schema."
            return response

        response.message = "Schema successfully fetched."
        response.data = entries

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/list",
    response_model=ResponseDefault,
    endpoint=list_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch all schema information",
)
