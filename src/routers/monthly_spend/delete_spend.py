from uuid import uuid4, UUID
from typing import Annotated
from utils.jwt import JWTHandler
from utils.query import QueryDatabase
from utils.helper import leap_year
from utils.helper import local_time
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, Path
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import (
    MonthlySchema, 
    CategorySchema, 
    MoneySpend
)
from utils.error import (
    ServiceError, 
    StashBaseApiError, 
    DataNotFoundError, 
    EntityDoesNotMatchedError
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Spend"], prefix="/spend")


async def delete_spend_endpoint(
    spend_id: UUID,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    spend_id = str(spend_id)
    current_time = local_time()
    query = QueryDatabase(db)

    try:
        money_spend_record = await query.find(table=MoneySpend, spend_id=spend_id)
        
        if not money_spend_record:
            raise DataNotFoundError(detail=f"Data not found.")

        await query.update(
            table=MoneySpend,
            condition={"spend_id":spend_id},
            data={"deleted_at": current_time},
        )
        response.message = "Daily spend sucessfully deleted."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/delete/{spend_id}",
    response_model=ResponseDefault,
    endpoint=delete_spend_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Delete spesific daily spend.",
)