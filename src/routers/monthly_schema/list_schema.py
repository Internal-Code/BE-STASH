from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from services.postgres.models import MonthlySchema
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.query.general import find_record
from utils.custom_error import ServiceError, StashBaseApiError

router = APIRouter(tags=["Monthly Schema"])


async def list_schema_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    entries = await find_record(
        db=db, table=MonthlySchema, fetch_type="all", unique_id=current_user.unique_id, deleted_at=None
    )
    try:
        if entries:
            response.message = f"Fetched {len(entries)} data."
            response.data = entries
            return response

        response.message = "User is not created scheema."

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/schema/list",
    response_model=ResponseDefault,
    endpoint=list_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch all schema information",
)
