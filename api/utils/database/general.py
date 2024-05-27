from pytz import timezone
from loguru import logger
from sqlalchemy import select
from datetime import datetime
from sqlalchemy.engine.cursor import CursorResult
from api.database.databaseModel import money_spend_schema
from api.database.databaseConnection import database_connection


def localTime(zone: str = "Asia/Jakarta") -> datetime:
    time = datetime.now(timezone(zone))
    return time

def createCategoryFormat(
    month: int, 
    year: int, 
    category: str, 
    budget: int, 
    updateAt: datetime = None
) -> dict:
    return {
        "createdAt": localTime(),
        "updatedAt": updateAt,
        "month": month,
        "year": year,
        "category": category,
        "budget": budget
    }

async def filterSpesificCategory(category: str) -> bool:

    res = False

    try:
        async with database_connection().connect() as session:
            logger.info("Connected PostgreSQL to perform filter spesific category")
            query = select(money_spend_schema).where(money_spend_schema.c.category == category)
            result = await session.execute(query)
            checked = result.scalar_one_or_none()
            if checked:
                res = True
            else:
                res = False
    except Exception as E:
        res = False
        logger.error(f"Error while filtering spesific category availability: {E}.")
    return res


async def filterMonthYearCategory(
    category: str,
    month: int = localTime().month,
    year: int = localTime().year
) -> bool:
    
    res = False

    try:
        async with database_connection().connect() as session:
            logger.info("Connected PostgreSQL to perform category availability validation.")
            logger.info("Filter with category.")
            query = select(money_spend_schema)\
                .where(money_spend_schema.c.month == month)\
                .where(money_spend_schema.c.year == year)\
                .where(money_spend_schema.c.category == category)
            result = await session.execute(query)
            checked = result.scalar_one_or_none()
            if checked:
                res = True
            else:
                res = False
    except Exception as E:
        res = False
        logger.error(f"Error while filtering spesific category availability: {E}.")
    return res
        

async def filterMonthYear(
    month: int = localTime().month,
    year: int = localTime().year
) -> bool:
    
    res = False

    try:
        async with database_connection().connect() as session:
            logger.info("Connected PostgreSQL to perform category availability validation.")
            logger.info("Filter with category.")
            query = select(money_spend_schema)\
                .where(money_spend_schema.c.month == month)\
                .where(money_spend_schema.c.year == year)
            result = await session.execute(query)
            checked = result.fetchone()
            if checked:
                res = True
            else:
                res = False
    except Exception as E:
        res = False
        logger.error(f"Error while filtering spesific category availability: {E}.")
    return res