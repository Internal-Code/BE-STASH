from pydantic import BaseModel
from typing import Literal, Any, Optional


class SelectData(BaseModel):
    entry: list[Any]


class Filters(BaseModel):
    operator: Literal["and", "or", "not"] = "and"
    filter_type: Literal[
        "gte",
        "gt",
        "lte",
        "le",
        "equal",
        "not_equal",
        "between",
        "like",
        "in",
        "is_not_null",
        "is_null",
        "not_in",
    ] = "equal"
    field_name: Any = None
    value: Any = ""
    filters: Optional[list["Filters"]] = []

    def to_log(self) -> dict[str, Any]:
        """Return a readable dict representation for logging."""
        if hasattr(self.field_name, "key"):
            field_name = self.field_name.key
        elif hasattr(self.field_name, "name"):
            field_name = self.field_name.name
        else:
            field_name = str(self.field_name)

        return {
            "operator": self.operator,
            "filter_type": self.filter_type,
            "field_name": field_name,
            "value": str(self.value),
        }
