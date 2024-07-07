from pydantic import EmailStr
from pytz import timezone
from src.auth.routers.dependencies import logging
from sqlalchemy import select, or_
from datetime import datetime
from src.database.models import money_spend_schema, money_spend, user
from src.database.connection import database_connection

def local_time(zone: str = "Asia/Jakarta") -> datetime:
    time = datetime.now(timezone(zone))
    return time

def create_category_format(
    category: str, 
    month: int = local_time().month, 
    year: int = local_time().year, 
    budget: int = 0,
    updated_at: datetime = None
) -> dict:
    return {
        "created_at": local_time(),
        "updated_at": updated_at,
        "month": month,
        "year": year,
        "category": category,
        "budget": budget
    }
    
def create_spending_format(
    category: str,
    description: str,
    amount: int = 0,
    spend_day: int = local_time().day,
    spend_month: int = local_time().month,
    spend_year: int = local_time().year,
    updated_at: datetime = None
) -> dict:
    return {
        "created_at": local_time(),
        "updated_at": updated_at,
        "spend_day": spend_day,
        "spend_month": spend_month,
        "spend_year": spend_year,
        "category": category,
        "description": description,
        "amount": amount
    }

def register_account_format(
    first_name: str,
    last_name: str,
    username: str,
    email: EmailStr,
    password: str,
    is_disabled: bool=False,
    updated_at: datetime = None
) -> dict:
    return {
        "created_at": local_time(),
        "updated_at": updated_at,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "password": password,
        'is_disabled': is_disabled
    }

async def filter_spesific_category(category: str) -> bool:

    res = False

    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Connected PostgreSQL to perform filter spesific category")
                query = select(money_spend_schema).where(money_spend_schema.c.category == category)
                result = await session.execute(query)
                checked = result.scalar_one_or_none()
                if checked:
                    res = True
            except Exception as E:
                logging.error(f"Error during filter_spesific_category: {E}.")
                await session.rollback()
                res = False
            finally:
                await session.close()
    except Exception as E:
        res = False
        logging.error(f"Error after filter_spesific_category: {E}.")
    return res


async def filter_month_year_category(
    category: str,
    month: int = local_time().month,
    year: int = local_time().year
) -> bool:
    
    res = False

    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with category, month and year.")
                query = select(money_spend_schema)\
                    .where(money_spend_schema.c.month == month)\
                    .where(money_spend_schema.c.year == year)\
                    .where(money_spend_schema.c.category == category)
                result = await session.execute(query)
                checked = result.scalar_one_or_none()
                if checked:
                    res = True
            except Exception as E:
                logging.error(f"Error during filter_month_year_category: {E}.")
                await session.rollback()
                res = False
            finally:
                await session.close()
    except Exception as E:
        res = False
        logging.error(f"Error after filter_month_year_category: {E}.")
    return res
        
async def filter_daily_spending(
    amount:int,
    category: str,
    description: str,
    spend_day:int = local_time().day,
    spend_month:int = local_time().month,
    spend_year:int = local_time().year
) -> bool:
    
    res = False
    try:
        async with database_connection().connect() as session:
            try:
                query = select(money_spend)\
                    .where(money_spend.c.spend_day == spend_day)\
                    .where(money_spend.c.spend_month == spend_month)\
                    .where(money_spend.c.spend_year == spend_year)\
                    .where(money_spend.c.amount == amount)\
                    .where(money_spend.c.description == description)\
                    .where(money_spend.c.category == category)
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    res = True
            except Exception as E:
                logging.error(f"Error during filtering spesific daily spend {spend_day}/{spend_month}/{spend_year} {category}/{description}/{amount}: {E}.")
                await session.rollback()
                res = False
            finally:
                await session.close()
    except Exception as E:
        res = False
        logging.error(f"Error after filtering spesific daily spending: {E}.")
    return res

async def filter_month_year(
    month: int = local_time().month,
    year: int = local_time().year
) -> bool:
    
    res = False

    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with month and year.")
                query = select(money_spend_schema)\
                    .where(money_spend_schema.c.month == month)\
                    .where(money_spend_schema.c.year == year)
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    res = True
            except Exception as E:
                logging.error(f"Error during filter_month_year category availability: {E}.")
                await session.rollback()
                res = False
            finally:
                await session.close()
    except Exception as E:
        res = False
        logging.error(f"Error after filter_month_year availability: {E}.")
    return res

async def filter_registered_user(
    username: str,
    email: EmailStr   
) -> bool:
    
    res = False
    
    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with username and email")
                query = select(user).where(
                    or_(
                        user.c.username == username,
                        user.c.email == email
                    )
                )
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    logging.warning(f"Account with username: {username} or email: {email} already registered. Please create an another account")
                    res = True
            except Exception as E:
                logging.error(f"Error during filter_registered_user category availability: {E}.")
                await session.rollback()
                res = False
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after filter_registered_user availability: {E}.")
        res = False
        
    return res