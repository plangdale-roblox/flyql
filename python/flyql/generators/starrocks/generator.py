import re
from typing import List, Mapping, Optional, Tuple, Union, Any

from flyql.core.exceptions import FlyqlError
from flyql.core.expression import Expression
from flyql.core.constants import Operator
from flyql.core.tree import Node

from flyql.generators.clickhouse.field import Field
from flyql.generators.clickhouse.helpers import validate_operation

OPERATOR_TO_CLICKHOUSE_FUNC = {
    Operator.EQUALS.value: "equals",
    Operator.NOT_EQUALS.value: "notEquals",
    Operator.EQUALS_REGEX.value: "match",
    Operator.NOT_EQUALS_REGEX.value: "match",
    Operator.GREATER_THAN.value: "greater",
    Operator.LOWER_THAN.value: "less",
    Operator.GREATER_OR_EQUALS_THAN.value: "greaterOrEquals",
    Operator.LOWER_OR_EQUALS_THAN.value: "lessOrEquals",
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
        func = OPERATOR_TO_CLICKHOUSE_FUNC[expression.operator]
        field_name = expression.key.segments[0]
        if field_name not in fields:
            raise FlyqlError(f"unknown field: {field_name}")
        field = fields[field_name]

        if field.normalized_type is not None:
            validate_operation(
                expression.value, field.normalized_type, expression.operator
            )

        if field.jsonstring:
            json_path = expression.key.segments[1:]
            json_path_str = ", ".join([escape_param(x) for x in json_path])

            str_value = escape_param(expression.value)
            multi_if = [
                f"JSONType({field.name}, {json_path_str}) = 'String', {func}(JSONExtractString({field.name}, {json_path_str}), {str_value})"
            ]
            if is_number(expression.value) and expression.operator not in [
                Operator.EQUALS_REGEX.value,
                Operator.NOT_EQUALS_REGEX.value,
            ]:
                multi_if.extend(
                    [
                        f"JSONType({field.name}, {json_path_str}) = 'Int64', {func}(JSONExtractInt({field.name}, {json_path_str}), {expression.value})",
                        f"JSONType({field.name}, {json_path_str}) = 'Double', {func}(JSONExtractFloat({field.name}, {json_path_str}), {expression.value})",
                        f"JSONType({field.name}, {json_path_str}) = 'Bool', {func}(JSONExtractBool({field.name}, {json_path_str}), {expression.value})",
                    ]
                )
            multi_if.append("0")
            multi_if_str = ",".join(multi_if)
            text = f"{reverse_operator}multiIf({multi_if_str})"
        elif field.is_json:
            json_path = expression.key.segments[1:]
            for part in json_path:
                validate_json_path_part(part)
            json_path_str = ".".join(f"`{part}`" for part in json_path)
            value = escape_param(expression.value)
            text = f"{field.name}.{json_path_str} {expression.operator} {value}"
        elif field.is_map:
            map_key = ":".join(expression.key.segments[1:])
            value = escape_param(expression.value)
            text = f"{reverse_operator}{func}({field.name}['{map_key}'], {value})"
        elif field.is_array:
            array_index_str = ":".join(expression.key.segments[1:])
            try:
                array_index = int(array_index_str)
            except Exception:
                raise FlyqlError(
                    f"invalid array index, expected number: {array_index_str}"
                )
            value = escape_param(expression.value)
            text = f"{reverse_operator}{func}({field.name}[{array_index}], {value})"
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
            text = f"match({field.name}, {value})"
        elif expression.operator == Operator.NOT_EQUALS_REGEX.value:
            value = escape_param(str(expression.value))
            text = f"not match({field.name}, {value})"
        elif expression.operator in [Operator.EQUALS.value, Operator.NOT_EQUALS.value]:
            operator = expression.operator
            is_like_pattern, value = prepare_like_pattern_value(str(expression.value))
            value = escape_param(value)
            if is_like_pattern:
                if expression.operator == Operator.EQUALS.value:
                    operator = "LIKE"
                else:
                    operator = "NOT LIKE"
            text = f"{field.name} {operator} {value}"
        else:
            if isinstance(expression.value, (int, float)):
                value = str(expression.value)
            else:
                value = escape_param(str(expression.value))
            text = f"{field.name} {expression.operator} {value}"
    return text


def to_sql(root: Node, fields: Mapping[str, Field]) -> str:
    """
    Returns ClickHouse WHERE clause for given tree and fields
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
