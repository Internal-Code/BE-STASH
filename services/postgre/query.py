from sqlmodel import SQLModel
from services.postgre.schema import Filters
from sqlalchemy.dialects import postgresql
from typing import Optional, Literal
from errors.custom_error import QueryError
from sqlalchemy import select, not_, and_, or_


class DatabaseQuery:
    def __init__(self, session):
        self.session = session

    def to_alias(self, field_names: list):
        return [
            f"{field_name.table.name}.{field_name.name}" for field_name in field_names
        ]

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
            case "like":
                return field.like(f"%{value}%")
            case "gt":
                return field > value
            case "gte":
                return field >= value
            case "lt":
                return field < value
            case "lte":
                return field <= value
            case "between":
                return field.between(value[0], value[1])
            case "in":
                return field.in_(value)
            case _:
                raise NotImplementedError(f"Unsupported filter type: {filter_type}")

    async def fetch(
        self,
        master_table: SQLModel,
        field_names: list = "*",
        join_tables: Optional[list] = None,
        filters: Optional[Filters] = None,
        group_by: Optional[list] = None,
        order_by: Optional[dict] = None,
        fetch_type: Literal["one", "all"] = "all",
    ):
        statement = select(master_table) if field_names == "*" else select(*field_names)

        if join_tables:
            for join in join_tables:
                join_to = join["table_name"]
                relations = join["column_relation"]

                for relation in relations:
                    statement = statement.select_from(master_table).join(
                        join_to, relation, isouter=True
                    )

        if filters:
            try:
                final_condition = self.build_condition(filters)
                statement = statement.where(final_condition)
            except Exception as e:
                raise QueryError("Invalid filter structure", errors={"filters": str(e)})

        if group_by:
            statement = statement.group_by(*group_by)

        if order_by:
            for o in order_by:
                field_name = o["field_name"]
                order_type = o["order_type"]

                if order_type == "asc":
                    statement = statement.order_by(field_name.asc())
                else:
                    statement = statement.order_by(field_name.desc())

        try:
            result = await self.session.execute(statement)
            print(
                statement.compile(
                    dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
                )
            )

            if fetch_type == "all":
                rows = result.fetchall()
                return [row[0].dict() for row in rows] if rows else None
            else:
                row = result.first()
                print(row)
                return dict(zip(self.to_alias(field_names), row)) if row else None
        except Exception as e:
            raise QueryError("Querry error", errors={"errors": str(e)})
