from pytz import timezone
from pydantic import EmailStr
from sqlalchemy import select
from uuid_extensions import uuid7
from sqlalchemy.engine.row import Row
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql import and_, update
from datetime import datetime, timedelta
from utils.logger import logging
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import (
    money_spend_schemas,
    money_spends,
    users,
    blacklist_tokens,
    user_tokens,
    reset_pins,
    send_otps,
)
from services.postgres.connection import database_connection


def local_time(zone: str = "UTC") -> datetime:
    time = datetime.now(timezone(zone))
    return time


async def filter_spesific_category(user_uuid: uuid7, category: str) -> bool:  # used
    try:
        async with database_connection().connect() as session:
            try:
                logging.info("Connected PostgreSQL to perform filter spesific category")
                query = select(money_spend_schemas).where(
                    money_spend_schemas.c.category == category,
                    money_spend_schemas.c.user_uuid == user_uuid,
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
) -> bool:  # used
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
) -> Row | None:  # used
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
) -> bool:  # used
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


async def is_using_registered_field(
    session: AsyncSession, table_name: Table, field: str, value: str
) -> bool:  # used
    try:
        query = select(table_name).where(getattr(table_name.c, field) == value)
        result = await session.execute(query)
        record = result.fetchone()
        if record:
            return True
    except Exception as e:
        logging.error(f"Error while checking {field}: {e}")
    return False


async def is_using_registered_email(email: EmailStr) -> bool:  # used
    if not email:
        return False

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


async def is_using_registered_phone_number(phone_number: str) -> bool:  # used
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


async def is_access_token_blacklisted(access_token: str) -> bool:  # used
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


async def is_refresh_token_blacklisted(refresh_token: str) -> bool:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = select(blacklist_tokens).where(
                    blacklist_tokens.c.refresh_token == refresh_token
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


async def save_tokens(
    user_uuid: uuid7, access_token: str, refresh_token: str
) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = user_tokens.insert().values(
                    created_at=local_time(),
                    user_uuid=user_uuid,
                    access_token=access_token,
                    refresh_token=refresh_token,
                )
                await session.execute(query)
                await session.commit()
                logging.info(
                    f"User {user_uuid} successfully saved tokens into database."
                )
            except Exception as E:
                logging.error(f"Error while save_tokens: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after save_tokens: {E}")
    return None


async def save_reset_pin_data(user_uuid: uuid7, email: EmailStr = None) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = reset_pins.insert().values(
                    user_uuid=user_uuid,
                    created_at=local_time(),
                    email=email,
                    save_to_hit_at=local_time() + timedelta(minutes=1),
                    blacklisted_at=local_time() + timedelta(minutes=5),
                )
                await session.execute(query)
                await session.commit()

                logging.info(
                    "User successfully insert reset password id into database."
                )

            except Exception as E:
                logging.error(f"Error while save_reset_password_id: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after save_reset_password_id: {E}")
    return None


async def extract_reset_pin_data(user_uuid: uuid7) -> Row | None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    select(reset_pins)
                    .where(reset_pins.c.user_uuid == user_uuid)
                    .order_by(reset_pins.c.created_at.desc())
                )
                result = await session.execute(query)
                latest_data = result.fetchone()

                if latest_data:
                    return latest_data
                logging.error(f"User {user_uuid} not found.")
            except Exception as E:
                logging.error(f"Error during extract_reset_pin_data: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after extract_reset_pin_data: {E}")
    return None


async def extract_tokens(user_uuid: uuid7) -> Row | None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    select(user_tokens)
                    .where(user_tokens.c.user_uuid == user_uuid)
                    .order_by(user_tokens.c.created_at.desc())
                )
                result = await session.execute(query)
                latest_record = result.fetchone()
                if latest_record is not None:
                    return latest_record
            except Exception as E:
                logging.error(f"Error during extract_tokens: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after extract_tokens: {E}")
    return None


async def save_google_sso_account(
    user_uuid: uuid7,
    email: EmailStr,
    full_name: str = None,
    phone_number: str = None,
    pin: str = None,
    is_email_verified: bool = True,
    is_phone_number_verified: bool = False,
) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = users.insert().values(
                    user_uuid=user_uuid,
                    created_at=local_time(),
                    full_name=full_name,
                    email=email,
                    phone_number=phone_number,
                    pin=pin,
                    verified_email=is_email_verified,
                    verified_phone_number=is_phone_number_verified,
                )
                await session.execute(query)
                await session.commit()
                logging.info("User google sso successfully saved data into database.")
            except Exception as E:
                logging.error(f"Error while save_google_sso_account: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after save_google_sso_account: {E}")
    return None


async def reset_user_pin(user_uuid: uuid7, changed_pin: str) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    update(users)
                    .where(users.c.user_uuid == user_uuid)
                    .values(updated_at=local_time(), pin=changed_pin)
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully saved reset pin id into database.")
            except Exception as E:
                logging.error(f"Error while reset_user_pin: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after reset_user_pin: {E}")
    return None


async def save_otp_data(
    user_uuid: uuid7,
    current_api_hit: int = None,
    otp_number: str = None,
    saved_by_system: bool = False,
    save_to_hit_at: datetime = local_time() + timedelta(minutes=1),
) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = send_otps.insert().values(
                    created_at=local_time(),
                    updated_at=None,
                    user_uuid=user_uuid,
                    otp_number=otp_number,
                    current_api_hit=current_api_hit,
                    saved_by_system=saved_by_system,
                    save_to_hit_at=save_to_hit_at,
                    blacklisted_at=local_time() + timedelta(minutes=3),
                    hit_tomorrow_at=local_time() + timedelta(days=1),
                )

                await session.execute(query)
                await session.commit()

            except Exception as E:
                logging.error(f"Error while save_otp_phone_number_verification: {E}")
                await session.rollback()
            finally:
                await session.close()

    except Exception as E:
        logging.error(f"Error after save_otp_phone_number_verification: {E}")
    return None


async def update_otp_data(
    user_uuid: uuid7,
    save_to_hit_at: datetime = local_time(),
    blacklisted_at: datetime = local_time(),
    hit_tomorrow_at: datetime = local_time(),
) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    send_otps.update()
                    .where(send_otps.c.user_uuid == user_uuid)
                    .values(
                        current_api_hit=1,
                        save_to_hit_at=save_to_hit_at,
                        blacklisted_at=blacklisted_at,
                        hit_tomorrow_at=hit_tomorrow_at,
                    )
                )

                await session.execute(query)
                await session.commit()

            except Exception as E:
                logging.error(f"Error while save_otp_phone_number_verification: {E}")
                await session.rollback()
            finally:
                await session.close()

    except Exception as E:
        logging.error(f"Error after save_otp_phone_number_verification: {E}")
    return None


async def extract_data_otp(user_uuid: uuid7) -> Row | None:  # used
    try:
        async with database_connection().connect() as session:
            async with session.begin():
                try:
                    query = (
                        select(send_otps)
                        .where(send_otps.c.user_uuid == user_uuid)
                        .order_by(send_otps.c.created_at.desc())
                        .with_for_update()
                    )
                    result = await session.execute(query)
                    latest_record = result.fetchone()
                    if latest_record:
                        logging.info("Data otp found.")
                        return latest_record

                    logging.info("Data otp not found.")
                except Exception as e:
                    logging.error(f"Error during extract_phone_number_otp: {e}")
                    await session.rollback()
                finally:
                    await session.close()
    except Exception as e:
        logging.error(f"Error after extract_phone_number_otp: {e}")
    return None


async def update_phone_number_status(user_uuid: uuid7) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(verified_phone_number=True, updated_at=local_time())
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully updated phone number status.")
            except Exception as E:
                logging.error(f"Error update_phone_number_status: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after update_phone_number_status: {E}")
    return None


async def update_verify_email_status(user_uuid: uuid7) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(verified_email=True, updated_at=local_time())
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully updated email status.")
            except Exception as E:
                logging.error(f"Error update_verify_email_status: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after update_verify_email_status: {E}")
    return None


async def update_user_phone_number(user_uuid: uuid7, phone_number: str) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(phone_number=phone_number, updated_at=local_time())
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully updated phone number.")
            except Exception as E:
                logging.error(f"Error update_user_phone_number: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after update_user_phone_number: {E}")
    return None


async def update_user_pin(user_uuid: uuid7, pin: str) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(pin=pin, updated_at=local_time())
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully updated pin.")
            except Exception as E:
                logging.error(f"Error update_user_pin: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after update_user_pin: {E}")
    return None


async def update_user_email(
    user_uuid: uuid7, email: EmailStr, verified_email: bool
) -> None:  # used
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(
                        email=email,
                        updated_at=local_time(),
                        verified_email=verified_email,
                    )
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully added email.")
            except Exception as E:
                logging.error(f"Error update_user_email: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after update_user_email: {E}")
    return None
