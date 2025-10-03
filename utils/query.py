from utils.logger import logging
from typing import Literal, Any, Union
from sqlmodel import SQLModel
from sqlalchemy import select, insert, update, delete, and_, or_
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from errors.custom_error import QueryError, NotFoundError


class QueryDatabase:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find(
        self,
        table: type[SQLModel],
        fetch: Literal["one", "all"] = "one",
        filter: Literal["and", "or"] = "and",
        order_by: Literal["asc", "desc"] = "asc",
        **kwargs: Any,
    ) -> Union[list[dict], Row, None]:
        condition = []

        if kwargs:
            for col, value in kwargs.items():
                col_attr = getattr(table, col, None)
                if not col_attr:
                    raise ValueError(f"Column {col} not found in {table.__tablename__} table!")
                condition.append(col_attr == value)
        try:
            filter_condition = or_(*condition) if filter == "or" else and_(*condition)
            order_clause = table.id.asc() if order_by == "asc" else table.id.desc()
            query = select(table).where(filter_condition).order_by(order_clause)
            result = await self._session.execute(query)

            if fetch == "all":
                rows = result.fetchall()
                return [dict(record) for entry in rows for record in entry] if rows else None
            else:
                return result.fetchone()
        except Exception as e:
            logging.error(f"Failed to find record in table {table.__name__}: {e}")
            await self._session.rollback()
            raise QueryError(detail="Database query error.")

    async def insert(self, table: type[SQLModel], data: dict) -> None:
        for column in data.keys():
            if not hasattr(table, column):
                raise ValueError(f"Column '{column}' not found in {table.__tablename__} table!")

        try:
            query = insert(table).values(**data)
            await self._session.execute(query)
            await self._session.commit()
            logging.info(f"New record inserted in table {table.__name__}.")
        except Exception as e:
            logging.error(f"Failed to insert record in table {table.__name__}: {e}")
            await self._session.rollback()
            raise QueryError(detail="Database query error.")

    async def update(self, table: type[SQLModel], condition: dict, data: dict) -> None:
        record = await self.find(table=table, **condition)

        try:
            if not condition:
                raise ValueError("Conditions must be a non-empty dictionary.")

            if not data:
                raise ValueError("Data must be a non-empty dictionary.")

            if not record:
                raise NotFoundError("Data not found.")

            for column in data.keys():
                if not hasattr(table, column):
                    raise ValueError(f"Column {column} not found in {table.__tablename__} table!")

            for column in condition.keys():
                if not hasattr(table, column):
                    raise ValueError(f"Column {column} not found in {table.__tablename__} table!")

            query = update(table).where(*(getattr(table, column) == value for column, value in condition.items())).values(**data)
            await self._session.execute(query)
            await self._session.commit()
            logging.info(f"Updated record in table {table.__name__}.")

        except ValueError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logging.error(f"Failed to update record in table {table.__name__} with conditions {condition}: {e}")
            raise QueryError(detail="Database query error.")

    async def delete(self, table: type[SQLModel]) -> None:
        try:
            query = delete(table)
            await self._session.execute(query)
            await self._session.commit()
            logging.info(f"Successfully deleted all records in table {table.__name__}.")
        except Exception as e:
            logging.error(f"Failed to delete all records in table {table.__name__}: {e}")
            await self._session.rollback()
            raise QueryError(detail="Database query error.")
