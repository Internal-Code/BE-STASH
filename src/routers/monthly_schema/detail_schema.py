from typing import Annotated
from utils.jwt import JWTHandler
from utils.query import QueryDatabase
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import MonthlySchema
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, Path
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def detail_schema_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year must be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)
    year = int(year)
    entries = await query.find(
        table=MonthlySchema,
        fetch="all",
        unique_id=current_user.unique_id,
        month=month,
        year=year,
        deleted_at=None,
    )

    try:
        if entries:
            response.message = f"Success fetched data."
            response.data = entries
            return response

        response.message = "User is not created category."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/detail/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=detail_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch schema information on spesific month.",
)
