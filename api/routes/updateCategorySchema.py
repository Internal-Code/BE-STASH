from loguru import logger
from fastapi import APIRouter, status
from api.utils.database.general import filterMonthYearCategory, filterSpesificCategory
from api.models.response import ResponseDefault
from api.utils.requestFormat import UpdateCategorySchema, localTime
from api.database.databaseConnection import database_connection
from api.database.databaseModel import money_spend_schema

router = APIRouter(tags=["schema"])

async def updateCategorySchema(schema: UpdateCategorySchema) -> ResponseDefault:
    
    response = ResponseDefault()
    isAvailable = await filterMonthYearCategory(
        month=schema.month,
        year=schema.year,
        category=schema.category
    )
    checkSpesificCategory = await filterSpesificCategory(category=schema.changedCategoryInto)

    try:
        if isAvailable is False:
            response.statusCode = status.HTTP_404_NOT_FOUND
            response.success = False
            response.message = f"Category {schema.category} not found. Please create category first."
        else:
            if checkSpesificCategory is False:
                logger.info("Endpoint update category.")
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
            else:
                logger.warning(f"Cannot changed category into: {schema.changedCategoryInto}.")
                response.statusCode = status.HTTP_400_BAD_REQUEST
                response.success = False
                response.message = f"Category {schema.changedCategoryInto} already saved. Please change with another category."
    except Exception as E:
        logger.error(f"Error while updating category: {E}.")
        response.statusCode = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.success = False
        response.message = f"Internal Server Error: {E}."
    
    return response

router.add_api_route(
    methods=["PATCH"],
    path="/update_category", 
    response_model=ResponseDefault,
    endpoint=updateCategorySchema
)

# TODO: FIX WHEN schema.changedCategoryInto filled with value is already on database