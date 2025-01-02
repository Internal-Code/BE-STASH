from utils.logger import logging
from sqlmodel import SQLModel
from sqlalchemy import select, insert, update
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from utils.custom_error import DatabaseError


async def find_record(db: AsyncSession, table: type[SQLModel], column: str, value: str) -> Row | None:
    column = getattr(table, column, None)

    if not column:
        raise ValueError(f"Column {column} not found in {table.__tablename__} table!")

    try:
        query = select(table).where(column == value)
        result = await db.execute(query)
        row = result.fetchone()
    except Exception as e:
        logging.error(f"Failed to find record in table {table.__name__}: {e}")
        await db.rollback()
        raise DatabaseError(detail="Database query error.")

    return row


async def insert_record(db: AsyncSession, table: type[SQLModel], data: dict) -> None:
    for column in data.keys():
        if not hasattr(table, column):
            raise ValueError(f"Column '{column}' not found in {table.__tablename__} table!")

    try:
        query = insert(table).values(**data)
        await db.execute(query)
        await db.commit()
        logging.info(f"New record inserted in table {table.__name__}.")
    except Exception as e:
        logging.error(f"Failed to insert record in table {table.__name__}: {e}")
        await db.rollback()
        raise DatabaseError(detail="Database query error.")


async def update_record(db: AsyncSession, table: type[SQLModel], conditions: dict, data: dict) -> None:
    for column in data.keys():
        if not hasattr(table, column):
            raise ValueError(f"Column '{column}' not found in {table.__name__} table!")

    for column in conditions.keys():
        if not hasattr(table, column):
            raise ValueError(f"Column '{column}' not found in {table.__name__} table!")

    try:
        query = (
            update(table)
            .where(*(getattr(table, column) == value for column, value in conditions.items()))
            .values(**data)
        )
        await db.execute(query)
        await db.commit()
        logging.info(f"Updated record in table {table.__name__}.")
    except Exception as e:
        logging.error(f"Failed to update record in table {table.__name__} with conditions {conditions}: {e}")
        await db.rollback()
        raise DatabaseError(detail="Database query error.")
