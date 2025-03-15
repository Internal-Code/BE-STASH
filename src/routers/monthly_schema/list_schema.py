from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from services.postgres.models import MonthlySchema
from src.schema.response import ResponseDefault
from utils.jwt import JWTHandler
from utils.query import QueryDatabase
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def list_schema_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)

    entries = await query.find(
        table=MonthlySchema,
        fetch="all",
        unique_id=current_user.unique_id,
        deleted_at=None,
    )

    try:
        if entries:
            response.message = "Sucess fetched data."
            response.data = entries
            return response

        response.message = "User is not created schema."

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
