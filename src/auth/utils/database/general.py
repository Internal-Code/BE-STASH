import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.schema import Table
from sqlalchemy.engine.row import Row
from uuid_extensions import uuid7
from sqlalchemy.sql import and_
from pydantic import EmailStr
from pytz import timezone
from sqlalchemy import select, update
from datetime import datetime
from fastapi import HTTPException, status
from src.auth.utils.logging import logging
from src.database.models import (
    money_spend_schemas,
    money_spends,
    users,
    blacklist_tokens,
)
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
    updated_at: datetime = None,
) -> dict:
    return {
        "created_at": local_time(),
        "updated_at": updated_at,
        "user_uuid": user_uuid,
        "month": month,
        "year": year,
        "category": category,
        "budget": budget,
    }


def create_spending_format(
    user_uuid: uuid7,
    category: str,
    description: str,
    amount: int = 0,
    spend_day: int = local_time().day,
    spend_month: int = local_time().month,
    spend_year: int = local_time().year,
    updated_at: datetime = None,
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
        "amount": amount,
    }


def register_account_format(
    first_name: str,
    last_name: str,
    username: str,
    email: EmailStr,
    password: str,
    updated_at: datetime = None,
) -> dict:
    return {
        "user_uuid": uuid7(),
        "created_at": local_time(),
        "updated_at": updated_at,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "password": password,
        "last_login": local_time(),
    }


async def filter_spesific_category(category: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Connected PostgreSQL to perform filter spesific category")
                query = select(money_spend_schemas).where(
                    money_spend_schemas.c.category == category
                )
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    return True
            except Exception as E:
                logging.error(f"Error during filter_spesific_category: {E}.")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after filter_spesific_category: {E}.")
    return False


async def filter_month_year_category(
    user_uuid: uuid7,
    category: str,
    month: int = local_time().month,
    year: int = local_time().year,
) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with category, month and year.")
                query = select(money_spend_schemas).where(
                    and_(
                        money_spend_schemas.c.user_uuid == user_uuid,
                        money_spend_schemas.c.month == month,
                        money_spend_schemas.c.year == year,
                        money_spend_schemas.c.category == category,
                    )
                )
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    return True
            except Exception as E:
                logging.error(f"Error during filter_month_year_category: {E}.")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after filter_month_year_category: {E}.")
    return False


async def filter_daily_spending(
    user_uuid: uuid7,
    amount: int,
    category: str,
    description: str,
    spend_day: int = local_time().day,
    spend_month: int = local_time().month,
    spend_year: int = local_time().year,
) -> Row | None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    select(money_spends)
                    .where(
                        and_(
                            money_spends.c.spend_day == spend_day,
                            money_spends.c.spend_month == spend_month,
                            money_spends.c.spend_year == spend_year,
                            money_spends.c.amount == amount,
                            money_spends.c.description == description,
                            money_spends.c.category == category,
                            money_spends.c.user_uuid == user_uuid,
                        )
                    )
                    .order_by(money_spends.c.created_at.desc())
                )
                result = await session.execute(query)
                latest_record = result.fetchone()
                if latest_record:
                    return latest_record
            except Exception as E:
                logging.error(
                    f"Error during filtering spesific daily spend {spend_day}/{spend_month}/{spend_year} {category}/{description}/{amount}: {E}."
                )
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after filtering spesific daily spending: {E}.")
    return None


async def filter_month_year(
    user_uuid: uuid7, month: int = local_time().month, year: int = local_time().year
) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Filter with month and year.")
                query = select(money_spend_schemas).where(
                    and_(
                        money_spend_schemas.c.month == month,
                        money_spend_schemas.c.year == year,
                        money_spend_schemas.c.user_uuid == user_uuid,
                    )
                )
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    return True
            except Exception as E:
                logging.error(
                    f"Error during filter_month_year category availability: {E}."
                )
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after filter_month_year availability: {E}.")
    return False


async def filter_user_register(
    username: str, email: EmailStr, phone_number: str
) -> None:
    try:
        logging.info("Filtering username, email and phone number.")

        if await is_using_registered_email(email=email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already taken. Please use another email.",
            )
        if await is_using_registered_username(username=username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken. Please use another username.",
            )
        if await is_using_registered_phone_number(phone_number=phone_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already taken. Please use another phone number.",
            )

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"Error while filter_registered_user availability: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )


async def update_latest_login(username: str, email: EmailStr) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                await session.execute(
                    update(users)
                    .where(
                        and_(
                            users.c.username == username,
                            users.c.email == email,
                        )
                    )
                    .values(last_login=local_time())
                )
                await session.commit()
                logging.info(f"Updated last_login for users {username}.")
                return True
            except Exception as e:
                logging.error(f"Error during update_latest_login: {e}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as e:
        logging.error(f"Error after update_latest_login: {e}")

    return False


async def is_phone_number_registered(phone_number: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(users).where(users.c.phone_number == phone_number)
                result = await session.execute(query)
                checked = result.fetchone()
                logging.error(
                    f"Phone number :{phone_number} already saved in database."
                )
                if checked:
                    return True
            except Exception as e:
                logging.error(f"Error during is_phone_num_registered: {e}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as e:
        logging.error(f"Error after is_phone_num_registered: {e}")

    return False


async def check_phone_number(value: str) -> str:
    if not value.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must contain only digits",
        )
    if not 10 <= len(value) <= 13:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be between 10 and 13 digits long",
        )
    return value


async def check_username(value: str) -> str:
    if len(value) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 5 characters long.",
        )
    return value


async def check_password(value: str) -> str:
    if len(value) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )
    if not re.search(r"[A-Z]", value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter.",
        )
    if not re.search(r"[a-z]", value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter.",
        )
    if not re.search(r"[0-9]", value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number.",
        )
    if not re.search(r"[\W_]", value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character.",
        )
    return value


async def is_using_registered_field(
    session: AsyncSession, table_name: Table, field: str, value: str
) -> bool:
    try:
        query = select(table_name).where(getattr(table_name.c, field) == value)
        result = await session.execute(query)
        return result.fetchone() is not None
    except Exception as e:
        logging.error(f"Error while checking {field}: {e}")
        raise


async def is_using_registered_email(email: EmailStr) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                result = await is_using_registered_field(
                    session=session, table_name=users, field="email", value=email
                )
                if result:
                    return True
            except Exception as E:
                logging.error(f"Error while is_using_registered_email: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after is_using_registered_email: {E}")

    return False


async def is_using_registered_phone_number(phone_number: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                result = await is_using_registered_field(
                    session=session,
                    table_name=users,
                    field="phone_number",
                    value=phone_number,
                )
                if result:
                    return True
            except Exception as E:
                logging.error(f"Error while is_using_registered_phone_number: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after is_using_registered_phone_number: {E}")

    return False


async def is_using_registered_username(username: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                result = await is_using_registered_field(
                    session=session, table_name=users, field="username", value=username
                )
                if result:
                    return True
            except Exception as E:
                logging.error(f"Error while is_using_registered_username: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after is_using_registered_username: {E}")

    return False


async def is_access_token_blacklisted(access_token: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(blacklist_tokens).where(
                    blacklist_tokens.c.access_token == access_token,
                )
                result = await session.execute(query)
                checked = result.fetchone()
                if checked:
                    return True
            except Exception as E:
                logging.error(f"Error while is_token_blacklisted: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after is_token_blacklisted: {E}")

    return False


async def is_refresh_token_blacklisted(refresh_token: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(blacklist_tokens).where(
                    blacklist_tokens.c.refresh_token == refresh_token
                )

                result = await session.execute(query)
                checked = result.fetchone()
                print("data refresh token", checked)
                if checked:
                    return True
            except Exception as E:
                logging.error(f"Error while is_token_blacklisted: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after is_token_blacklisted: {E}")

    return False
