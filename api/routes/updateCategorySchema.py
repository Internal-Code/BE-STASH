from loguru import logger
from fastapi import APIRouter, status
from api.utils.database.general import checkCategoryAvaibility
from api.models.response import ResponseDefault
from api.utils.requestFormat import UpdateCategorySchema, localTime
from api.database.databaseConnection import database_connection
from api.database.databaseModel import money_spend_schema

router = APIRouter(tags=["schema"])

async def updateCategorySchema(schema: UpdateCategorySchema) -> ResponseDefault:
    
    response = ResponseDefault()
    isAvailable = await checkCategoryAvaibility(
        month=schema.month,
        year=schema.year,
        category=schema.category
    )

    try:
        if isAvailable is False:
            response.statusCode = status.HTTP_404_NOT_FOUND
            response.success = False
            response.message = f"Category {schema.category} not found. Please create category first."
        else:
            logger.info("Endpoint delete category.")
            async with database_connection().connect() as session:
                async with session.begin():
                    query = money_spend_schema.update()\
                        .where(money_spend_schema.c.month == schema.month)\
                        .where(money_spend_schema.c.year == schema.year)\
                        .where(money_spend_schema.c.category == schema.category)\
                        .values(
                            updatedAt = localTime(),
                            category = schema.changedCategoryInto
                        )
                    await session.execute(query)
                    await session.commit()
                    logger.info(f"Updated category {schema.category} into {schema.changedCategoryInto}.")
            response.message = "Update category success."
    except Exception as E:
        logger.error(f"Error while updating category: {E}.")
        response.statusCode = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.success = False
        response.message = f"Internal Server Error: {E}."
    
    return response

router.add_api_route(
    methods=["PATCH"],
    path="/api/v1/update_category", 
    response_model=ResponseDefault,
    endpoint=updateCategorySchema
)

# TODO: FIX WHEN schema.changedCategoryInto filled with value is already on database