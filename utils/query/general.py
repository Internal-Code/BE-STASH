from utils.logger import logging
from typing import Literal, Any
from sqlmodel import SQLModel
from sqlalchemy import select, insert, update, delete, and_, or_
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from utils.custom_error import DatabaseQueryError, DataNotFoundError


async def find_record(
    db: AsyncSession,
    table: type[SQLModel],
    fetch_type: Literal["one", "all"] = "one",
    filter_type: Literal["and", "or"] = "and",
    order_by: Literal["asc", "desc"] = "asc",
    **kwargs: Any,
) -> list[Row] | Row | None:
    condition = []
    if kwargs:
        for col, value in kwargs.items():
            col_attr = getattr(table, col, None)
            if not col_attr:
                raise ValueError(f"Column {col} not found in {table.__tablename__} table!")

            condition.append(col_attr == value)

    try:
        filter_condition = or_(*condition) if filter_type == "or" else and_(*condition)
        order_clause = table.id.asc() if order_by == "asc" else table.id.desc()
        query = select(table).where(filter_condition).order_by(order_clause)
        result = await db.execute(query)

        if fetch_type == "all":
            rows = result.fetchall()
            entries = [dict(row._mapping) for row in rows] if rows else None
            return entries
        else:
            entry = result.fetchone()
            return entry
    except Exception as e:
        logging.error(f"Failed to find record in table {table.__name__}: {e}")
        await db.rollback()
        raise DatabaseQueryError(detail="Database query error.")


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
        raise DatabaseQueryError(detail="Database query error.")


async def update_record(db: AsyncSession, table: type[SQLModel], conditions: dict, data: dict) -> None:
    target_records = await find_record(db=db, table=table, **conditions)

    try:
        if not conditions:
            raise ValueError("Conditions cannot be empty")

        if not data:
            raise ValueError("Data must be a non-empty dictionary.")

        if not target_records:
            raise DataNotFoundError("Data not found.")

        for column in data.keys():
            if not hasattr(table, column):
                raise ValueError(f"Column {column} not found in {table.__tablename__} table!")

        for column in conditions.keys():
            if not hasattr(table, column):
                raise ValueError(f"Column {column} not found in {table.__tablename__} table!")

        query = (
            update(table)
            .where(*(getattr(table, column) == value for column, value in conditions.items()))
            .values(**data)
        )
        await db.execute(query)
        await db.commit()
        logging.info(f"Updated record in table {table.__name__}.")
    except ValueError:
        raise
    except DataNotFoundError:
        raise
    except Exception as e:
        logging.error(f"Failed to update record in table {table.__name__} with conditions {conditions}: {e}")
        raise DatabaseQueryError(detail="Database query error.")


async def delete_record(db: AsyncSession, table: type[SQLModel]) -> None:
    try:
        query = delete(table)
        await db.execute(query)
        await db.commit()
        logging.info(f"Successfully deleted all records in table {table.__name__}.")
    except Exception as e:
        logging.error(f"Failed to delete all records in table {table.__name__}: {e}")
        await db.rollback()
        raise DatabaseQueryError(detail="Database query error.")
