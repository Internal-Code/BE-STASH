from utils.logger import logging
from utils.query import QueryDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.model import Country
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends
from utils.error import ServiceError, StashBaseApiError, DataNotFoundError

router = APIRouter(tags=["User Management"], prefix="/user/management")


async def get_country_endpoint(db: AsyncSession = Depends(get_db)) -> ResponseDefault:
    logging.info("Fetch country data endpdoint.")
    query = QueryDatabase(db)
    response = ResponseDefault()

    try:
        country_record = await query.find(Country, fetch="all")

        if not country_record:
            logging.error("Country data not found.")
            raise DataNotFoundError(detail="Country data not found.")

        response.message = "Success extract country data."
        response.data = country_record

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/country",
    response_model=ResponseDefault,
    endpoint=get_country_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch country data.",
)
