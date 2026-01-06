from typing import Any
from flyql.core.exceptions import FlyqlError
from flyql.core.constants import VALID_KEY_VALUE_OPERATORS
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
    ) -> None:
        if operator not in VALID_KEY_VALUE_OPERATORS:
            raise FlyqlError(f"invalid operator: {operator}")

        if not key.segments:
            raise FlyqlError("emtpy key")

        self.key = key
        self.operator = operator
        if not value_is_string:
            self.value: Any = try_convert_to_number(value)
        else:
            self.value = value

    def __str__(self) -> str:
        return f"{self.key.raw}{self.operator}{self.value}"
