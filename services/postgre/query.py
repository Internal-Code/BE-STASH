from typing import Optional, Literal, Union, Type, Any
from errors.custom_error import QueryError
from utils.logger import logging
from services.postgre.query_schema import Filters, SelectData
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    update,
    select,
    not_,
    and_,
    or_,
    insert,
    inspect,
)


class DatabaseQuery:
    def __init__(self, session: AsyncSession):
        self.session = session

    def build_condition(self, filter_block: Filters):
        if filter_block.filters:
            conditions = [
                self.build_condition(sub_filter) for sub_filter in filter_block.filters
            ]
            operator = filter_block.operator

            match operator:
                case "and":
                    return and_(*conditions)
                case "or":
                    return or_(*conditions)
                case "not":
                    if len(conditions) != 1:
                        raise ValueError("NOT operator must have exactly one condition")
                    return not_(conditions[0])
                case _:
                    raise NotImplementedError(
                        f"Unsupported logical operator: {operator}"
                    )

        field = filter_block.field_name
        value = filter_block.value
        filter_type = filter_block.filter_type

        match filter_type:
            case "equal":
                return field == value
            case "not_equal":
                return field != value
            case "like":
                return field.like(value)
            case "gt":
                return field > value
            case "gte":
                return field >= value
            case "le":
                return field < value
            case "lte":
                return field <= value
            case "between":
                try:
                    if isinstance(value, tuple) and len(value) == 2:
                        return field.between(value[0], value[1])
                    else:
                        raise ValueError(
                            "Value for 'between' must be a tuple of two elements. Example: (10, 20)"
                        )
                except Exception as e:
                    raise QueryError("Query error", {"errors": str(e)})
            case "in":
                return field.in_(value)
            case "is_not_null":
                return field.isnot(None)
            case "is_null":
                return field.is_(None)
            case "not_in":
                return field.notin_(value)
            case _:
                raise NotImplementedError(f"Unsupported filter type: {filter_type}")

    async def fetch(
        self,
        master_table: Type[SQLModel],
        field_names: Union[SelectData, Literal["*"]] = "*",
        join_tables: Optional[SelectData] = None,
        filters: Optional[Filters] = None,
        group_by: Optional[SelectData] = None,
        having: Optional[Filters] = None,
        order_by: Optional[SelectData] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        subquery: bool = False,
        fetch_type: Literal["all", "one"] = "all",
    ):
        try:
            if field_names == "*":
                statement = select(master_table)
                table_columns = [
                    c.key for c in inspect(master_table).mapper.column_attrs
                ]
                aliases = [
                    f"{master_table.__tablename__}.{col}" for col in table_columns
                ]
            else:
                fields = field_names.entry
                statement = select(*fields)
                aliases = []
                for field in fields:
                    try:
                        if hasattr(field, "class_") and hasattr(field, "key"):
                            table_name = field.class_.__tablename__
                            column_name = field.key
                            aliases.append(f"{table_name}.{column_name}")
                        elif hasattr(field, "name"):
                            aliases.append(str(field.name).lower())
                        else:
                            aliases.append(str(field).lower())
                    except Exception:
                        aliases.append(str(field).lower())

            if join_tables:
                for entry in join_tables.entry:
                    data = len(entry)
                    match data:
                        case 2:
                            join_table, join_condition = entry
                            join_type = "left"
                        case 3:
                            join_table, join_condition, join_type = entry
                        case _:
                            raise ValueError(
                                "Each join entry must be on this format [table, field, join_type]. (Default: left join.)"
                            )

                    if join_type == "left":
                        statement = statement.select_from(master_table).join(
                            join_table, join_condition, isouter=True
                        )
                    elif join_type == "inner":
                        statement = statement.select_from(master_table).join(
                            join_table, join_condition, isouter=False
                        )
                    else:
                        raise ValueError("join_type must be 'inner' or 'left'")

            # WHERE clause
            if filters:
                condition = self.build_condition(filters)
                statement = statement.where(condition)

            # GROUP BY clause
            if group_by:
                statement = statement.group_by(*group_by.entry)

            # HAVING clause
            if having:
                having_condition = self.build_condition(having)
                statement = statement.having(having_condition)

            # ORDER BY clause
            if order_by:
                if not isinstance(order_by.entry, list):
                    raise ValueError(
                        "Order by must be a list of column and order_type (column, direction). Example: [Users.id, 'asc']"
                    )

                for column, direction in order_by.entry:
                    if direction.lower() == "asc":
                        statement = statement.order_by(column.asc())
                    else:
                        statement = statement.order_by(column.desc())

            # LIMIT
            if limit:
                statement = statement.limit(limit)

            # OFFSET 👈 NEW
            if offset:
                statement = statement.offset(offset)

            if subquery:
                try:
                    subq = statement.subquery()
                    result = await self.session.execute(statement)
                    rows = (
                        result.scalars().all()
                        if field_names == "*"
                        else result.fetchall()
                    )
                    data = (
                        [row.model_dump() for row in rows]
                        if field_names == "*"
                        else [dict(zip(aliases, row)) for row in rows]
                    )
                    if not data:
                        data = None
                    return subq, data
                except Exception as e:
                    raise QueryError(message="Subquery error.", error={"subquery": e})

            result = await self.session.execute(statement)

            # Return results
            if fetch_type == "all":
                rows = (
                    result.scalars().all() if field_names == "*" else result.fetchall()
                )
                return (
                    [row.model_dump() for row in rows]
                    if field_names == "*"
                    else [dict(zip(aliases, row)) for row in rows]
                )
            else:
                row = result.scalars().first() if field_names == "*" else result.first()
                return (
                    row.model_dump()
                    if field_names == "*" and row
                    else dict(zip(aliases, row))
                    if row
                    else None
                )

        except Exception as e:
            raise QueryError("Query error", {"errors": str(e)})

    async def insert(
        self, table: Type[SQLModel], data: Union[dict[str, Any], list[Any], SQLModel]
    ) -> None:
        try:
            if isinstance(data, dict):
                query = insert(table).values(**data)
                await self.session.execute(query)
            elif isinstance(data, SQLModel):
                self.session.add(data)
            elif isinstance(data, list) and all(isinstance(d, dict) for d in data):
                query = insert(table).values(data)
                await self.session.execute(query)
            elif isinstance(data, list) and all(isinstance(d, SQLModel) for d in data):
                self.session.add_all(data)

            else:
                raise ValueError("Unsupported data type for insert")

            await self.session.commit()
        except Exception as e:
            logging.error(f"Failed to insert record in table {table.__name__}: {e}")
            await self.session.rollback()
            raise QueryError("Database query error.", {"errors": str(e)})

    async def update(
        self,
        master_table: Type[SQLModel],
        values: dict[str, Any],
        filters: Optional["Filters"] = None,
    ) -> int:
        """
        Dynamically update rows in a table, similar to how fetch builds queries.

        :param master_table: Table model to update
        :param values: Dict of column -> new value
        :param filters: Optional Filters object (same as fetch)
        :return: Number of rows updated
        """
        try:
            # Start UPDATE statement
            stmt = update(master_table).values(**values)

            # WHERE clause if filters provided
            if filters:
                condition = self.build_condition(filters)
                stmt = stmt.where(condition)

            # Execute update
            result = await self.session.execute(stmt)
            await self.session.commit()

            rowcount = result.rowcount or 0
            logging.info(
                f"Updated {rowcount} record(s) in {master_table.__tablename__} "
                f"with values={values} and filters={filters.model_dump() if filters else None}"
            )
            return rowcount

        except Exception as e:
            logging.error(
                f"Failed to update record(s) in table {master_table.__name__}: {e}"
            )
            await self.session.rollback()
            raise QueryError("Database query error.", {"errors": str(e)})
