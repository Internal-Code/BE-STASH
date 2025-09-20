from pydantic import BaseModel, Field, model_validator
from typing import Literal, Any, Optional


class JoinTables(BaseModel):
    table_name: Any = Field(description="Example: Employees")
    column_relation: list[Any] = Field(
        description="Example: [Employees.id == Projects.project_id]"
    )

    @model_validator(mode="after")
    def validate_relations(self) -> "JoinTables":
        tables = []
        master_table = self.table_name.__tablename__.lower()

        for expr in self.column_relation:
            try:
                left_table = expr.left.table.name
                right_table = expr.right.table.name
            except AttributeError:
                raise ValueError(
                    "Invalid column_relation: each element must be a SQLAlchemy binary expression"
                )

            tables.extend([left_table, right_table])

        if master_table not in tables:
            raise ValueError(
                f"One of the tables in column_relation must relate to master table: '{master_table}'. "
                f"Found: {tables}"
            )

        return self


class Filters(BaseModel):
    operator: Optional[Literal["and", "or", "not"]] = None
    filter_type: Optional[
        Literal["gte", "gt", "lte", "le", "equal", "between", "like", "in"]
    ] = None
    field_name: Optional[Any] = None
    value: Optional[Any] = None
    filters: Optional[list["Filters"]] = None

    class Config:
        arbitrary_types_allowed = True


class OrderBy(BaseModel):
    field_name: Any = Field(description="Example: Employees.created_at")
    order_type: Literal["asc", "desc"] = Field(
        description="Example: Employees.created_at.desc()"
    )
