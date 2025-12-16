from typing import Set, Tuple, Any, Optional

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
    ("int", Operator.EQUALS_REGEX.value, "string"),
    ("float", Operator.EQUALS_REGEX.value, "string"),
    ("int", Operator.NOT_EQUALS_REGEX.value, "string"),
    ("float", Operator.NOT_EQUALS_REGEX.value, "string"),
    # Bool with comparison
    ("bool", Operator.LOWER_THAN.value, "bool"),
    ("bool", Operator.GREATER_THAN.value, "bool"),
    ("bool", Operator.GREATER_OR_EQUALS_THAN.value, "bool"),
    ("bool", Operator.LOWER_OR_EQUALS_THAN.value, "bool"),
}


def validate_operation(
    value: Any, field_normalized_type: Optional[str], operator: str
) -> None:
    if field_normalized_type is None:
        return

    if (field_normalized_type, operator, get_value_type(value)) in FORBIDDEN_OPERATIONS:
        raise FlyqlError(
            f"operation not allowed: {field_normalized_type} field with '{operator}' operator"
        )
