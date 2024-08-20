from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.schema import Table
from sqlalchemy.engine.row import Row
from uuid_extensions import uuid7
from sqlalchemy.sql import and_, update
from pydantic import EmailStr
from pytz import timezone
from sqlalchemy import select
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from src.auth.utils.logging import logging
from src.database.models import (
    money_spend_schemas,
    money_spends,
    users,
    blacklist_tokens,
    user_tokens,
    reset_pins,
    phone_number_otps,
)
from src.database.connection import database_connection


def local_time(zone: str = "UTC") -> datetime:
    time = datetime.now(timezone(zone))
    return time


async def create_category_format(
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


async def filter_spesific_category(user_uuid: uuid7, category: str) -> bool:
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


# async def filter_user_register(username: str, email: EmailStr) -> None:
#     try:
#         logging.info("Filtering username, email and phone number.")

#         if await is_using_registered_email(email=email):
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Email already taken. Please use another email.",
#             )
#         if await is_using_registered_username(username=username):
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Username already taken. Please use another username.",
#             )

#     except HTTPException as e:
#         raise e

#     except Exception as e:
#         logging.error(f"Error while filter_registered_user availability: {e}.")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal Server Error: {e}.",
#         )


async def check_phone_number(phone_number: str) -> str:
    if not phone_number.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must contain only digits.",
        )

    if not (10 <= len(phone_number) <= 13):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be between 10 or 13 digits long.",
        )

    return phone_number


async def check_pin(pin: str) -> str:
    if not pin.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pin number must contain only digits.",
        )

    if len(pin) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pin number must be 6 digits long.",
        )
    return pin


async def check_otp(otp: str) -> str:
    if not otp.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP number must contain only digits.",
        )

    if len(otp) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP number must be 6 digits long.",
        )
    return otp


async def check_fullname(value: str) -> str:
    value = " ".join(value.split())

    if not all(char.isalpha() or char.isspace() for char in value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fullname should contain only letters and spaces.",
        )

    if len(value) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fullname should be less than 100 character.",
        )

    fullname = value.title()

    return fullname


# async def check_password(value: str) -> str:
#     if len(value) == 0:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password cannot be empty.",
#         )
#     if len(value) < 8:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password must be at least 8 characters long.",
#         )
#     if not re.search(r"[A-Z]", value):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password must contain at least one uppercase letter.",
#         )
#     if not re.search(r"[a-z]", value):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password must contain at least one lowercase letter.",
#         )
#     if not re.search(r"[0-9]", value):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password must contain at least one number.",
#         )
#     if not re.search(r"[\W_]", value):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password must contain at least one special character.",
#         )
#     return value


async def is_using_registered_field(
    session: AsyncSession, table_name: Table, field: str, value: str
) -> bool:
    try:
        query = select(table_name).where(getattr(table_name.c, field) == value)
        result = await session.execute(query)
        record = result.fetchone()
        if record:
            return True
    except Exception as e:
        logging.error(f"Error while checking {field}: {e}")
    return False


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


async def save_tokens(user_uuid: uuid7, access_token: str, refresh_token: str) -> None:
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


async def save_reset_pin_data(user_uuid: uuid7, email: EmailStr = None) -> None:
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


async def extract_reset_pin_data(user_uuid: uuid7) -> Row | None:
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


async def extract_tokens(user_uuid: uuid7) -> Row | None:
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
) -> None:
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
                logging.info("User google ss0 successfully saved data into database.")
            except Exception as E:
                logging.error(f"Error while save_google_sso_account: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after save_google_sso_account: {E}")
    return None


async def save_user_pin(user_uuid: uuid7, user_pin: str) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(pin=user_pin)
                )
                await session.execute(query)
                await session.commit()
                logging.info(f"User {user_uuid} successfully saved pin into database.")
            except Exception as E:
                logging.error(f"Error while save_user_pin: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after save_user_pin: {E}")
    return None


async def verify_user_pin(user_uuid: uuid7, pin: str) -> bool:
    try:
        async with database_connection().connect() as session:
            try:
                query = select(users).where(
                    and_(users.c.user_uuid == user_uuid, users.c.pin == pin)
                )
                result = await session.execute(query)
                latest_record = result.fetchone()
                if latest_record is not None:
                    return latest_record
            except Exception as E:
                logging.error(f"Error during verify_user_pin: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after verify_user_pin: {E}")
    return None


async def reset_user_pin(user_uuid: uuid7, changed_pin: str) -> None:
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


async def save_phone_number(email: EmailStr, phone_number: str) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.email == email,
                    )
                    .values(phone_number=phone_number)
                )

                await session.execute(query)
                await session.commit()
                logging.info(
                    f"User {email} successfully update phone number into database."
                )
            except Exception as E:
                logging.error(f"Error while save_phone_number: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after save_phone_number: {E}")
    return None


async def save_otp_phone_number_verification(
    user_uuid: uuid7,
    current_api_hit: int = None,
    otp_number: str = None,
    saved_by_system: bool = False,
    save_to_hit_at: datetime = local_time() + timedelta(minutes=1),
) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = phone_number_otps.insert().values(
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


async def update_otp_phone_number_verification(
    user_uuid: uuid7,
    current_api_hit: int = None,
    otp_number: str = None,
    saved_by_system: bool = False,
    save_to_hit_at: datetime = datetime.now(timezone("UTC")) + timedelta(minutes=1),
    blacklisted_at: datetime = datetime.now(timezone("UTC")) + timedelta(minutes=3),
) -> None:
    try:
        async with database_connection().connect() as session:
            async with session.begin():
                try:
                    query = (
                        phone_number_otps.update()
                        .where(phone_number_otps.c.user_uuid == user_uuid)
                        .values(
                            created_at=local_time(),
                            current_api_hit=current_api_hit,
                            otp_number=otp_number,
                            save_to_hit_at=save_to_hit_at,
                            blacklisted_at=blacklisted_at,
                            saved_by_system=saved_by_system,
                        )
                    )
                    await session.execute(query)
                    await session.commit()
                except Exception as E:
                    logging.error(
                        f"Error while save_otp_phone_number_verification: {E}"
                    )
                    await session.rollback()
                finally:
                    await session.close()
    except Exception as E:
        logging.error(f"Error after save_otp_phone_number_verification: {E}")
    return None


async def extract_phone_number_otp(user_uuid: uuid7) -> Row | None:
    try:
        async with database_connection().connect() as session:
            async with session.begin():  # Start a transaction block
                try:
                    query = (
                        select(phone_number_otps)
                        .where(phone_number_otps.c.user_uuid == user_uuid)
                        .order_by(phone_number_otps.c.created_at.desc())
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
                    await session.rollback()  # Roll back the transaction on failure
                    raise e
                finally:
                    await session.close()  # Ensure the session is closed properly
    except Exception as e:
        logging.error(f"Error after extract_phone_number_otp: {e}")
    return None


async def update_phone_number_status(user_uuid: uuid7) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(verified_phone_number=True)
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


async def update_user_google_sso(
    user_uuid: uuid7, phone_number: str, full_name: str
) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(phone_number=phone_number, full_name=full_name)
                )
                await session.execute(query)
                await session.commit()
                logging.info("User successfully updated full name and phone number.")
            except Exception as E:
                logging.error(f"Error while update_user_google_sso: {E}")
                await session.rollback()
            finally:
                await session.close()
    except Exception as E:
        logging.error(f"Error after update_user_google_sso: {E}")
    return None


async def update_user_phone_number(user_uuid: uuid7, phone_number: str) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(phone_number=phone_number)
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


async def update_user_pin(user_uuid: uuid7, pin: str) -> None:
    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(
                        users.c.user_uuid == user_uuid,
                    )
                    .values(pin=pin)
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


async def verify_uuid(unique_id: uuid7) -> UUID:
    try:
        valid_uuid = UUID(unique_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format."
        )
    return valid_uuid
