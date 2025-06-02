from utils.logger import logging
from utils.query import QueryDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.model import Country
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import RegisterAccountPayload
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import ServiceError, StashBaseApiError, DataNotFoundError

router = APIRouter(tags=["User Management"], prefix="/user/management")


async def register_user_endpoint(schema: RegisterAccountPayload, background_tasks: BackgroundTasks,db: AsyncSession = Depends(get_db)) -> ResponseDefault:
    logging.info("Register user endpdoint.")
    query = QueryDatabase(db)
    response = ResponseDefault()

    try:
        country_record = await query.find(Country, fetch="all")
        
        if not country_record:
            logging.error("Country data not found.")
            raise DataNotFoundError("Country data not found.")
        
        id_record = [entry["id"] for entry in country_record]
        
        if schema.country_id not in id_record:
            raise DataNotFoundError("Country id not found in database.")

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["POST"],
    path="/register",
    response_model=ResponseDefault,
    endpoint=register_user_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Account registration.",
)
