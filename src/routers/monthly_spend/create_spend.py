from typing import Annotated
from utils.jwt import get_current_user
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from services.postgres.models import MonthlySchema, CategorySchema
from src.schema.request_format import CreateSpend
from utils.query.general import find_record, insert_record
from utils.custom_error import ServiceError, StashBaseApiError, DataNotFoundError

router = APIRouter(tags=["Monthly Spend"], prefix="/spend")


async def create_spend(
    schema: CreateSpend,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    schema_record = await find_record(db=db, table=MonthlySchema, month=schema.month, year=schema.year)
    print(schema_record.month_id)
    # is_available = await filter_month_year_category(
    #     user_uuid=current_user.user_uuid,
    #     month=schema.spend_month,
    #     year=schema.spend_year,
    #     category=schema.category,
    # )

    try:
        if not schema_record:
            raise DataNotFoundError("Monthly data not found.")
        category_record = await find_record(db=db, table=CategorySchema, category_id=schema_record.month_id)
        print(category_record)
        pass
        # logging.info("Endpoint create spend money.")
        # async with database_connection().connect() as session:
        #     try:
        #         if is_available is False:
        #             try:
        #                 logging.info(
        #                     f"Inserting data into table {money_spends.name} and {money_spend_schemas.name}"
        #                 )

        #                 create_spend = money_spends.insert().values(
        #                     created_at=local_time(),
        #                     updated_at=None,
        #                     user_uuid=current_user.user_uuid,
        #                     spend_day=schema.spend_day,
        #                     spend_month=schema.spend_month,
        #                     spend_year=schema.spend_year,
        #                     category=schema.category,
        #                     description=schema.description,
        #                     amount=schema.amount,
        #                 )
        #                 create_category = money_spend_schemas.insert().values(
        #                     created_at=local_time(),
        #                     updated_at=None,
        #                     user_uuid=current_user.user_uuid,
        #                     month=schema.spend_month,
        #                     year=schema.spend_year,
        #                     category=schema.category,
        #                     budget=0,
        #                 )
        #                 await session.execute(create_spend)
        #                 await session.execute(create_category)
        #                 await session.commit()
        #                 logging.info("Created new spend money and schema.")
        #                 response.message = "Created new spend money and schema data."
        #                 response.success = True
        #             except Exception as E:
        #                 logging.error(f"Error during creating new spend money and schema: {E}.")
        #                 await session.rollback()
        #                 raise DatabaseQueryError(detail=f"Database error: {E}.")
        #         else:
        #             try:
        #                 logging.info(f"Only inserting data into table {money_spends.name}")
        #                 create_spend = money_spends.insert().values(
        #                     created_at=local_time(),
        #                     updated_at=None,
        #                     user_uuid=current_user.user_uuid,
        #                     spend_day=schema.spend_day,
        #                     spend_month=schema.spend_month,
        #                     spend_year=schema.spend_year,
        #                     category=schema.category,
        #                     description=schema.description,
        #                     amount=schema.amount,
        #                 )
        #                 await session.execute(create_spend)
        #                 await session.commit()
        #                 logging.info("Created new spend money.")
        #                 response.message = "Created new spend money."
        #                 response.success = True
        #             except Exception as E:
        #                 logging.error(f"Error during creating new spend money: {E}.")
        #                 await session.rollback()
        #                 raise DatabaseQueryError(detail=f"Database error: {E}.")
        #     except Exception as E:
        #         logging.error(
        #             f"Error during creating spend money or with adding money schema: {E}."
        #         )
        #         await session.rollback()
        #         raise DatabaseQueryError(
        #             detail=f"Database error during creating spend money or with adding money schema: {E}."
        #         )
        #     finally:
        #         await session.close()
    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/create",
    response_model=ResponseDefault,
    endpoint=create_spend,
    status_code=status.HTTP_201_CREATED,
    summary="Create daily spend record.",
)
