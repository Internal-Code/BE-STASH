from uuid import UUID
from fastapi import APIRouter, status, Depends, Query
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from services.postgres.models import CategorySchema, MonthlySchema
from src.schema.response import ResponseDefault
from utils.jwt import JWTHandler
from utils.query import QueryDatabase
from utils.helper import local_time
from utils.error import ServiceError, StashBaseApiError, DataNotFoundError

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Category"], prefix="/category")


async def list_category_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
    month: str = Query(default=local_time().month, regex=r"^\d{2}$"),
    year: str = Query(default=str(local_time().year), regex=r"^\d{4}$")
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)


    category_entries = await query.find(
        table=CategorySchema,
        fetch="all",
        unique_id=current_user.unique_id,
        category_id=month,
        deleted_at=None,
    )

    try:
        if not category_entries:
            response.message = "No category data available."
            return response

        response.message = f"Fetched {len(category_entries)} data."
        response.data = category_entries

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/list/{month_id}",
    response_model=ResponseDefault,
    endpoint=list_category_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch all category information.",
)
