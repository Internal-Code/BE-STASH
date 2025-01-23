import pytest
from uuid import uuid4
from faker import Faker
from sqlalchemy.engine.row import Row
from services.postgres.connection import get_db
from utils.generator import Generator
from utils.error import DatabaseQueryError
from services.postgres.models import User
from utils.query import QueryDatabase


generator = Generator()
faker = Faker()


@pytest.mark.asyncio
async def test_find_all_record_with_available_data_and_no_filter():
    records_to_insert = [
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": generator.random_number(6),
        },
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": generator.random_number(6),
        },
    ]

    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        for record in records_to_insert:
            await query.insert(table=User, data=record)

        records = await query.find(table=User, fetch="all")

    assert len(records) == len(records_to_insert)
    assert type(records) is list
    for i, record in enumerate(records):
        assert record["unique_id"] == records_to_insert[i]["unique_id"]
        assert record["full_name"] == records_to_insert[i]["full_name"]
        assert record["phone_number"] == records_to_insert[i]["phone_number"]
        assert record["pin"] == records_to_insert[i]["pin"]


@pytest.mark.asyncio
async def test_find_all_record_with_available_data_and_single_filter():
    same_pin = generator.random_number(6)
    records_to_insert = [
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": same_pin,
        },
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": same_pin,
        },
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": generator.random_number(6),
        },
    ]

    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        for record in records_to_insert:
            await query.insert(table=User, data=record)

        records = await query.find(table=User, fetch="all", pin=same_pin)

    assert len(records) == 2
    assert type(records) is list
    normalized_fetched_data = {
        (
            record["unique_id"],
            record["full_name"],
            record["phone_number"],
            record["pin"],
        )
        for record in records
    }
    normalized_expected_data = {
        (
            record["unique_id"],
            record["full_name"],
            record["phone_number"],
            record["pin"],
        )
        for record in records_to_insert
        if record["pin"] == same_pin
    }

    assert normalized_fetched_data == normalized_expected_data


@pytest.mark.asyncio
async def test_find_all_record_with_available_data_and_multi_filter():
    pin = generator.random_number(6)
    phone_number = faker.phone_number()
    records_to_insert = [
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": phone_number,
            "pin": pin,
        },
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": pin,
        },
        {
            "unique_id": str(uuid4()),
            "full_name": faker.name(),
            "phone_number": faker.phone_number(),
            "pin": generator.random_number(6),
        },
    ]

    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        for record in records_to_insert:
            await query.insert(table=User, data=record)

        records = await query.find(
            table=User, fetch="all", pin=pin, phone_number=phone_number
        )

    assert len(records) == 1
    assert type(records) is list
    normalized_fetched_data = {
        (
            record["unique_id"],
            record["full_name"],
            record["phone_number"],
            record["pin"],
        )
        for record in records
    }
    normalized_expected_data = {
        (
            record["unique_id"],
            record["full_name"],
            record["phone_number"],
            record["pin"],
        )
        for record in records_to_insert
        if record["pin"] == pin and record["phone_number"] == phone_number
    }

    assert normalized_fetched_data == normalized_expected_data


@pytest.mark.asyncio
async def test_find_all_record_with_empty_data_and_no_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        records = await query.find(table=User, fetch="all")
    assert records is None


@pytest.mark.asyncio
async def test_find_all_record_with_empty_data_and_single_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        records = await query.find(
            table=User, fetch="all", pin=generator.random_number(6)
        )

    assert records is None


@pytest.mark.asyncio
async def test_find_all_record_with_empty_data_and_multi_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        records = await query.find(
            table=User,
            fetch="all",
            pin=generator.random_number(6),
            phone_number=faker.phone_number(),
        )
    assert records is None


@pytest.mark.asyncio
async def test_find_single_record_with_available_data_and_no_filter():
    unique_id = str(uuid4())
    full_name = faker.name()
    phone_number = faker.phone_number()
    pin = generator.random_number(6)

    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        await query.insert(
            table=User,
            data={
                "unique_id": unique_id,
                "full_name": full_name,
                "phone_number": phone_number,
                "pin": pin,
            },
        )

        records = await query.find(table=User)

    assert type(records) is Row
    assert records.unique_id == unique_id
    assert records.full_name == full_name
    assert records.phone_number == phone_number
    assert records.pin == pin


@pytest.mark.asyncio
async def test_find_single_record_with_available_data_and_single_filter():
    unique_id = str(uuid4())
    full_name = faker.name()
    phone_number = faker.phone_number()
    pin = generator.random_number(6)
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        await query.insert(
            table=User,
            data={
                "unique_id": unique_id,
                "full_name": full_name,
                "phone_number": phone_number,
                "pin": pin,
            },
        )

        records = await query.find(table=User, unique_id=unique_id)

    assert type(records) is Row
    assert records.unique_id == unique_id
    assert records.full_name == full_name
    assert records.phone_number == phone_number
    assert records.pin == pin


@pytest.mark.asyncio
async def test_find_single_record_with_available_data_and_multi_filter():
    unique_id = str(uuid4())
    full_name = faker.name()
    phone_number = faker.phone_number()
    pin = generator.random_number(6)
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        await query.insert(
            table=User,
            data={
                "unique_id": unique_id,
                "full_name": full_name,
                "phone_number": phone_number,
                "pin": pin,
            },
        )

        records = await query.find(
            table=User, unique_id=unique_id, phone_number=phone_number
        )

    assert type(records) is Row
    assert records.unique_id == unique_id
    assert records.full_name == full_name
    assert records.phone_number == phone_number
    assert records.pin == pin


@pytest.mark.asyncio
async def test_find_single_record_with_empty_data_and_no_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        records = await query.find(table=User)
    assert records is None


@pytest.mark.asyncio
async def test_find_single_record_with_empty_data_and_single_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        records = await query.find(table=User, pin=generator.random_number(6))
    assert records is None


@pytest.mark.asyncio
async def test_find_single_record_with_empty_data_and_multi_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        await query.delete(table=User)
        records = await query.find(
            table=User,
            fetch="all",
            pin=generator.random_number(6),
            phone_number=faker.phone_number(),
        )
    assert records is None


@pytest.mark.asyncio
async def test_find_single_record_raised_with_invalid_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        with pytest.raises(
            ValueError,
            match=f"Column invalid_column not found in {User.__name__.lower()} table!",
        ):
            await query.find(table=User, invalid_column="invalid_value")


@pytest.mark.asyncio
async def test_find_all_record_raised_with_invalid_filter():
    async for db in get_db():
        query = QueryDatabase(db)
        with pytest.raises(
            ValueError,
            match=f"Column invalid_column not found in {User.__name__.lower()} table!",
        ):
            await query.find(table=User, invalid_column="invalid_value", fetch="all")


@pytest.mark.asyncio
async def test_find_record_raised_database_query_error():
    async for db in get_db():
        query = QueryDatabase(db)
        with pytest.raises(DatabaseQueryError, match="Database query error."):
            await query.find(table=User, unique_id=uuid4())
