import pytest
from uuid import uuid4
from faker import Faker
from sqlalchemy.engine.row import Row
from services.postgres.models import User
from services.postgres.connection import get_db
from utils.custom_error import DataNotFoundError, DatabaseQueryError
from utils.generator import random_number, random_word
from utils.query.general import find_record, delete_record, insert_record, update_record


@pytest.mark.asyncio
async def test_update_record_with_available_data_inside_table():
    faker = Faker()
    unique_id = str(uuid4())
    old_full_name = faker.name()
    new_full_name = faker.name()
    old_pin = random_number(length=6)
    new_pin = random_number(length=6)
    old_email = faker.email()
    new_email = faker.email()
    old_phone_number = random_number(length=10)
    new_phone_number = random_number(length=10)

    async for db in get_db():
        await delete_record(db=db, table=User)
        await insert_record(
            db=db,
            table=User,
            data={
                "unique_id": unique_id,
                "full_name": old_full_name,
                "phone_number": old_phone_number,
                "email": old_email,
                "pin": old_pin,
            },
        )
        await update_record(
            db=db,
            table=User,
            conditions={"unique_id": unique_id},
            data={
                "unique_id": unique_id,
                "full_name": new_full_name,
                "phone_number": new_phone_number,
                "email": new_email,
                "pin": new_pin,
            },
        )
        updated_record = await find_record(db=db, table=User, unique_id=unique_id)

    assert updated_record is not None
    assert type(updated_record) is Row
    assert updated_record.full_name == new_full_name
    assert updated_record.email == new_email
    assert updated_record.phone_number == new_phone_number
    assert updated_record.pin == new_pin


@pytest.mark.asyncio
async def test_update_record_with_empty_conditions():
    faker = Faker()
    async for db in get_db():
        with pytest.raises(ValueError, match="Conditions cannot be empty"):
            await update_record(db=db, table=User, conditions={}, data={"full_name": faker.name()})


@pytest.mark.asyncio
async def test_update_record_with_empty_data():
    async for db in get_db():
        with pytest.raises(ValueError, match="Data must be a non-empty dictionary."):
            await update_record(db=db, table=User, conditions={"unique_id": str(uuid4())}, data={})


@pytest.mark.asyncio
async def test_update_record_with_random_conditions():
    random_column = random_word()
    random_value = random_word()
    async for db in get_db():
        with pytest.raises(ValueError, match=f"Column {random_column} not found in {User.__name__.lower()} table!"):
            await update_record(db=db, table=User, conditions={random_column: random_value}, data={})


@pytest.mark.asyncio
async def test_update_record_raised_database_query_error():
    async for db in get_db():
        with pytest.raises(DatabaseQueryError, match="Database query error."):
            await update_record(db=db, table=User, conditions={"unique_id": uuid4()}, data={})


@pytest.mark.asyncio
async def test_update_record_raised_data_not_found_error():
    async for db in get_db():
        with pytest.raises(DataNotFoundError, match="Data not found."):
            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": str(uuid4())},
                data={"phone_number": random_number(length=10)},
            )
