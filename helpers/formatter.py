from copy import deepcopy
from typing import Callable, Iterable, Optional, List, Any


class CustomFormatter:
    def _convert_field(
        self,
        data: Optional[List[dict[str, Any]]],
        field_names: Iterable[str],
        fn: Callable[[Any], Any],
    ) -> Optional[List[dict[str, Any]]]:
        if not data:
            return None

        converted = deepcopy(data)
        for row in converted:
            for field in field_names:
                if field in row and row[field] is not None:
                    try:
                        row[field] = fn(row[field])
                    except Exception:
                        pass
        return converted

    def to_int(
        self, data: Optional[List[dict[str, Any]]], *fields: str
    ) -> Optional[List[dict[str, Any]]]:
        return self._convert_field(data, fields, lambda v: int(v))
