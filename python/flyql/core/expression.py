from typing import Any, List, Optional
from flyql.core.exceptions import FlyqlError
from flyql.core.constants import VALID_KEY_VALUE_OPERATORS, Operator
from flyql.core.key import Key


def try_convert_to_number(value: str | int | float) -> str | int | float:
    try:
        f = float(value)
        if f.is_integer():
            return int(f)
        return f
    except ValueError:
        return value


class Expression:
    def __init__(
        self,
        key: Key,
        operator: str,
        value: str | int | float,
        value_is_string: bool | None,
        values: Optional[List[Any]] = None,
        values_type: Optional[str] = None,
    ) -> None:
        if operator not in VALID_KEY_VALUE_OPERATORS:
            raise FlyqlError(f"invalid operator: {operator}")

        if not key.segments:
            raise FlyqlError("emtpy key")

        self.key = key
        self.operator = operator
        self.values: Optional[List[Any]] = values
        self.values_type: Optional[str] = values_type

        if operator in (Operator.IN.value, Operator.NOT_IN.value):
            self.value: Any = None
        elif not value_is_string:
            self.value = try_convert_to_number(value)
        else:
            self.value = value

    def __str__(self) -> str:
        if self.operator in (Operator.IN.value, Operator.NOT_IN.value):
            return f"{self.key.raw} {self.operator} [{', '.join(str(v) for v in (self.values or []))}]"
        return f"{self.key.raw}{self.operator}{self.value}"
