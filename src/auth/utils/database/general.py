import re
from sqlalchemy.engine.row import Row
from uuid_extensions import uuid7
from sqlalchemy.sql import and_
from pydantic import EmailStr
from pytz import timezone
from sqlalchemy import select, or_, update
from datetime import datetime
from fastapi import HTTPException, status
from src.auth.utils.logging import logging
from src.database.models import money_spend_schema, money_spend, user
from src.database.connection import database_connection

def local_time(zone: str = "Asia/Jakarta") -> datetime:
    time = datetime.now(timezone(zone))
    return time

def create_category_format(
    category: str, 
    user_uuid: uuid7,
    month: int = local_time().month, 
    year: int = local_time().year, 
    budget: int = 0,
    updated_at: datetime = None
) -> dict:
    return {
        "created_at": local_time(),
        "updated_at": updated_at,
        "user_uuid": user_uuid,
        "month": month,
        "year": year,
        "category": category,
        "budget": budget
    }
    
def create_spending_format(
    user_uuid: uuid7,
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
        "user_uuid": user_uuid,
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
    is_deactivated: bool=False,
    updated_at: datetime = None
) -> dict:
    return {
        'user_uuid': uuid7(),
        "created_at": local_time(),
        "updated_at": updated_at,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "password": password,
        "is_deactivated": is_deactivated,
        "last_login": local_time()
    }

async def filter_spesific_category(category: str) -> bool:

    res = False

    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Connected PostgreSQL to perform filter spesific category")
                query = select(money_spend_schema).where(money_spend_schema.c.category == category)
                result = await session.execute(query)
                checked = result.fetchone()
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
    user_uuid: uuid7,
    category: str,
    month: int = local_time().month,
    year: int = local_time().year
) -> bool:
    
    res = False

    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with category, month and year.")
                query = select(money_spend_schema).where(
                    and_(
                        money_spend_schema.c.user_uuid==user_uuid,
                        money_spend_schema.c.month == month,
                        money_spend_schema.c.year == year,
                        money_spend_schema.c.category == category
                    )
                )
                result = await session.execute(query)
                checked = result.fetchone()
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
    user_uuid: uuid7,
    amount:int,
    category: str,
    description: str,
    spend_day:int = local_time().day,
    spend_month:int = local_time().month,
    spend_year:int = local_time().year
) -> Row|None:
    
    res = None
    try:
        async with database_connection().connect() as session:
            try:
                query = select(money_spend).where(
                    and_(
                        money_spend.c.spend_day == spend_day,
                        money_spend.c.spend_month == spend_month,
                        money_spend.c.spend_year == spend_year,
                        money_spend.c.amount == amount,
                        money_spend.c.description == description,
                        money_spend.c.category == category,
                        money_spend.c.user_uuid == user_uuid
                    )
                ).order_by(money_spend.c.created_at.desc())
                result = await session.execute(query)
                latest_record = result.fetchone()
                if latest_record:
                    res = latest_record
                    print(res)
            except Exception as E:
                logging.error(f"Error during filtering spesific daily spend {spend_day}/{spend_month}/{spend_year} {category}/{description}/{amount}: {E}.")
                await session.rollback()
                res = None
            finally:
                await session.close()
    except Exception as E:
        res = None
        logging.error(f"Error after filtering spesific daily spending: {E}.")
    return res

async def filter_month_year(
    user_uuid: uuid7,
    month: int = local_time().month,
    year: int = local_time().year
) -> bool:
    
    res = False

    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with month and year.")
                query = select(money_spend_schema).where(
                    and_(
                        money_spend_schema.c.month == month,
                        money_spend_schema.c.year == year,
                        money_spend_schema.c.user_uuid == user_uuid,
                    )   
                )
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

async def update_latest_login(username: str, email: EmailStr) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                await session.execute(
                    update(user).where(
                        and_(
                            user.c.username == username,
                            user.c.email == email,
                        )
                    ).values(last_login=local_time())
                )
                await session.commit()
                logging.info(f"Updated last_login for user {username}.")
                return True
            except Exception as e:
                logging.error(f"Error during update_latest_login: {e}")
                await session.rollback()
                return False
    except Exception as e:
        logging.error(f"Error connecting to database in update_latest_login: {e}")
    
    return False

async def check_password(value: str) -> str:
    if len(value) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one number.")
    if not re.search(r'[\W_]', value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one special character.")
    return value