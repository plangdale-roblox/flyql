from typing import Set, Tuple, Any, Optional, List

from flyql.core.exceptions import FlyqlError
from flyql.core.constants import Operator


def get_value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    else:
        return ""


IN_COMPATIBLE_TYPES: dict[str, set[str]] = {
    "string": {"string"},
    "int": {"int", "float"},
    "float": {"int", "float"},
    "bool": {"bool", "int"},
    "date": {"string"},
}


FORBIDDEN_OPERATIONS: Set[Tuple[str, str, str]] = {
    # String vs numbers comparison
    ("string", Operator.LOWER_THAN.value, "int"),
    ("string", Operator.LOWER_THAN.value, "float"),
    ("string", Operator.GREATER_THAN.value, "int"),
    ("string", Operator.GREATER_THAN.value, "float"),
    ("string", Operator.GREATER_OR_EQUALS_THAN.value, "int"),
    ("string", Operator.GREATER_OR_EQUALS_THAN.value, "float"),
    ("string", Operator.LOWER_OR_EQUALS_THAN.value, "int"),
    ("string", Operator.LOWER_OR_EQUALS_THAN.value, "float"),
    # Numbers with regex
    ("int", Operator.REGEX.value, "string"),
    ("float", Operator.REGEX.value, "string"),
    ("int", Operator.NOT_REGEX.value, "string"),
    ("float", Operator.NOT_REGEX.value, "string"),
    # Bool with comparison
    ("bool", Operator.LOWER_THAN.value, "bool"),
    ("bool", Operator.GREATER_THAN.value, "bool"),
    ("bool", Operator.GREATER_OR_EQUALS_THAN.value, "bool"),
    ("bool", Operator.LOWER_OR_EQUALS_THAN.value, "bool"),
}


def validate_operation(
    value: Any, column_normalized_type: Optional[str], operator: str
) -> None:
    if column_normalized_type is None:
        return

    if (
        column_normalized_type,
        operator,
        get_value_type(value),
    ) in FORBIDDEN_OPERATIONS:
        raise FlyqlError(
            f"operation not allowed: {column_normalized_type} column with '{operator}' operator"
        )


def validate_in_list_types(
    values: List[Any], column_normalized_type: Optional[str]
) -> None:
    if column_normalized_type is None:
        return

    if not values:
        return

    allowed_types = IN_COMPATIBLE_TYPES.get(column_normalized_type)
    if allowed_types is None:
        return

    for value in values:
        value_type = get_value_type(value)
        if value_type and value_type not in allowed_types:
            raise FlyqlError(
                f"type mismatch in IN list: {column_normalized_type} column cannot contain {value_type} values"
            )
