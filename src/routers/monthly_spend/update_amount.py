from uuid import UUID
from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.helper import local_time
from utils.query import QueryDatabase
from fastapi import APIRouter, status, Depends
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.model import MoneySpend
from src.schema.request_format import Amount
from src.schema.response import ResponseDefault
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    EntityForceInputSameDataError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Spend"], prefix="/spend")


async def update_amount_endpoint(
    spend_id: UUID,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    schema: Amount,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Update amount endpoint.")
    response = ResponseDefault()
    spend_id = str(spend_id)
    current_time = local_time()
    query = QueryDatabase(db)

    try:
        money_spend_record = await query.find(table=MoneySpend, spend_id=spend_id)

        if not money_spend_record:
            logging.error("Spend id not found.")
            raise DataNotFoundError(detail="Data not found.")

        if money_spend_record.amount == schema.amount:
            logging.error("Cannot update into same amount data.")
            raise EntityForceInputSameDataError(
                detail="Should update into different amount."
            )

        await query.update(
            table=MoneySpend,
            condition={"spend_id": spend_id},
            data={"updated_at": current_time, "amount": schema.amount},
        )
        response.message = "Daily spend sucessfully updated."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/update-amount/{spend_id}",
    response_model=ResponseDefault,
    endpoint=update_amount_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Update amount in spesific daily spend.",
)
