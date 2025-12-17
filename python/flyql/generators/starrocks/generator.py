import re
from typing import Mapping, Tuple, Any

from flyql.core.exceptions import FlyqlError
from flyql.core.expression import Expression
from flyql.core.constants import Operator
from flyql.core.tree import Node

from flyql.generators.starrocks.field import Field
from flyql.generators.starrocks.helpers import validate_operation

OPERATOR_TO_STARROCKS_OPERATOR = {
    Operator.EQUALS.value: "=",
    Operator.NOT_EQUALS.value: "!=",
    Operator.EQUALS_REGEX.value: "regexp",
    Operator.NOT_EQUALS_REGEX.value: "regexp",
    Operator.GREATER_THAN.value: ">",
    Operator.LOWER_THAN.value: "<",
    Operator.GREATER_OR_EQUALS_THAN.value: ">=",
    Operator.LOWER_OR_EQUALS_THAN.value: "<=",
}

LIKE_PATTERN_CHAR = "*"
SQL_LIKE_PATTERN_CHAR = "%"
JSON_KEY_PATTERN = re.compile(r"^[a-zA-Z_][.a-zA-Z0-9_-]*$")

ESCAPE_CHARS_MAP = {
    "\b": "\\b",
    "\f": "\\f",
    "\r": "\\r",
    "\n": "\\n",
    "\t": "\\t",
    "\0": "\\0",
    "\a": "\\a",
    "\v": "\\v",
    "\\": "\\\\",
    "'": "\\'",
}


def validate_json_path_part(part: str) -> None:
    if not part:
        raise FlyqlError("Invalid JSON path part")
    if not JSON_KEY_PATTERN.match(part):
        raise FlyqlError("Invalid JSON path part")


def escape_param(item: Any) -> str:
    if item is None:
        return "NULL"
    elif isinstance(item, str):
        return "'%s'" % "".join(ESCAPE_CHARS_MAP.get(c, c) for c in item)
    elif isinstance(item, bool):
        return str(item)
    elif isinstance(item, (int, float)):
        return str(item)
    else:
        return str(item)


def is_number(value: Any) -> bool:
    try:
        float(value)
    except (ValueError, TypeError):
        try:
            int(value)
        except (ValueError, TypeError):
            return False
        else:
            return True
    else:
        return True


def prepare_like_pattern_value(value: str) -> Tuple[bool, str]:
    pattern_found = False
    new_value = ""
    i = 0
    while i < len(value):
        char = value[i]
        if char == LIKE_PATTERN_CHAR:
            if i > 0 and value[i - 1] == "\\":
                new_value += LIKE_PATTERN_CHAR
            else:
                new_value += SQL_LIKE_PATTERN_CHAR
                pattern_found = True
        elif char == SQL_LIKE_PATTERN_CHAR:
            pattern_found = True
            new_value += "\\"
            new_value += SQL_LIKE_PATTERN_CHAR
        elif char == "\\" and i + 1 < len(value) and value[i + 1] == LIKE_PATTERN_CHAR:
            new_value += "\\"
        else:
            new_value += char
        i += 1
    return pattern_found, new_value


def expression_to_sql(expression: Expression, fields: Mapping[str, Field]) -> str:
    text = ""

    if expression.key.is_segmented:
        reverse_operator = ""
        if expression.operator == Operator.NOT_EQUALS_REGEX.value:
            reverse_operator = "not "
        operator = OPERATOR_TO_STARROCKS_OPERATOR[expression.operator]
        field_name = expression.key.segments[0]
        if field_name not in fields:
            raise FlyqlError(f"unknown field: {field_name}")
        field = fields[field_name]

        if field.normalized_type is not None:
            validate_operation(
                expression.value, field.normalized_type, expression.operator
            )

        # Although any column can be marked as jsonstring, and this can provide UI
        # benefits in Telescope, we cannot actually cast Map and Array columns to JSON
        # as we can in Clickhouse. Additionally, there is no benefit in casting a JSON
        # column to JSON again. Therefore, we only do jsonstring parsing for other
        # column types.
        if field.is_json:
            # Although `parse_json` works on a JSON field, it is more efficient to not use it
            # when we know the field is already the JSON type.
            json_path = expression.key.segments[1:]
            for part in json_path:
                validate_json_path_part(part)
            json_path_str = "->".join(f"'{part}'" for part in json_path)
            value = escape_param(expression.value)

            field_exp = f"`{field.name}`->{json_path_str}"

            if (
                expression.operator == Operator.EQUALS_REGEX.value
                or expression.operator == Operator.NOT_EQUALS_REGEX.value
            ):
                field_exp = f"cast({field_exp} as string)"
            text = f"{field_exp} {reverse_operator}{operator} {value}"
        elif field.is_map:
            map_path = expression.key.segments[1:]
            map_key = "']['".join(map_path)
            value = escape_param(expression.value)
            text = f"`{field.name}`['{map_key}'] {reverse_operator}{operator} {value}"
        elif field.is_array:
            array_index_str = ":".join(expression.key.segments[1:])
            try:
                array_index = int(array_index_str)
            except Exception:
                raise FlyqlError(
                    f"invalid array index, expected number: {array_index_str}"
                )
            value = escape_param(expression.value)
            text = f"`{field.name}`[{array_index}] {reverse_operator}{operator} {value}"
        elif field.jsonstring:
            json_path = expression.key.segments[1:]
            for part in json_path:
                validate_json_path_part(part)
            json_path_str = "->".join(f"'{part}'" for part in json_path)
            value = escape_param(expression.value)
            text = f"parse_json(`{field.name}`)->{json_path_str} {reverse_operator}{operator} {value}"
        else:
            raise FlyqlError("path search for unsupported field type")

    else:
        field_name = expression.key.segments[0]
        if field_name not in fields:
            raise FlyqlError(f"unknown field: {field_name}")

        field = fields[field_name]

        if field.values and str(expression.value) not in field.values:
            raise FlyqlError(f"unknown value: {expression.value}")

        if field.normalized_type is not None:
            validate_operation(
                expression.value, field.normalized_type, expression.operator
            )

        if expression.operator == Operator.EQUALS_REGEX.value:
            value = escape_param(str(expression.value))
            text = f"regexp(`{field.name}`, {value})"
        elif expression.operator == Operator.NOT_EQUALS_REGEX.value:
            value = escape_param(str(expression.value))
            text = f"not regexp(`{field.name}`, {value})"
        elif expression.operator in [Operator.EQUALS.value, Operator.NOT_EQUALS.value]:
            operator = expression.operator
            is_like_pattern, value = prepare_like_pattern_value(str(expression.value))
            value = escape_param(value)
            if is_like_pattern:
                if expression.operator == Operator.EQUALS.value:
                    operator = "LIKE"
                else:
                    operator = "NOT LIKE"
            text = f"`{field.name}` {operator} {value}"
        else:
            if isinstance(expression.value, (int, float)):
                value = str(expression.value)
            else:
                value = escape_param(str(expression.value))
            text = f"`{field.name}` {expression.operator} {value}"
    return text


def to_sql(root: Node, fields: Mapping[str, Field]) -> str:
    """
    Returns Starrocks WHERE clause for given tree and fields
    """
    left = ""
    right = ""
    text = ""

    if root.expression is not None:
        text = expression_to_sql(expression=root.expression, fields=fields)

    if root.left is not None:
        left = to_sql(root=root.left, fields=fields)

    if root.right is not None:
        right = to_sql(root=root.right, fields=fields)

    if len(left) > 0 and len(right) > 0:
        text = f"({left} {root.bool_operator} {right})"
    elif len(left) > 0:
        text = left
    elif len(right) > 0:
        text = right

    return text
