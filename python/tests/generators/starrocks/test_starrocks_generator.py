import pytest
from flyql.core.exceptions import FlyqlError
from flyql.core.expression import Expression
from flyql.core.constants import Operator
from flyql.core.tree import Node
from flyql.core.key import parse_key
from flyql.generators.starrocks.column import Column
from flyql.generators.starrocks.generator import (
    expression_to_sql,
    to_sql,
    escape_param,
    is_number,
    prepare_like_pattern_value,
)


@pytest.fixture
def fields() -> dict[str, Column]:
    return {
        "message": Column("message", False, "String"),
        "count": Column("count", False, "Largeint"),
        "price": Column("price", False, "Float"),
        "active": Column("active", False, "Bool"),
        "created_at": Column("created_at", False, "DateTime"),
        "json_field": Column("json_field", True, "String"),
        "new_json": Column("new_json", False, "JSON"),
        "tags": Column("tags", False, "Array<String>"),
        "metadata": Column("metadata", False, "Map<String, String>"),
        "user_info": Column("user_info", False, "Struct<name:String,age:Int>"),
    }


class TestEscapeParam:

    def test_escape_string(self) -> None:
        assert escape_param("hello") == "'hello'"
        assert escape_param("test'quote") == "'test\\'quote'"
        assert escape_param("test\\backslash") == "'test\\\\backslash'"
        assert escape_param("test\nNewline") == "'test\\nNewline'"

    def test_escape_none(self) -> None:
        assert escape_param(None) == "NULL"

    def test_escape_numbers(self) -> None:
        assert escape_param(123) == "123"
        assert escape_param(12.34) == "12.34"
        assert escape_param(True) == "True"
        assert escape_param(False) == "False"


class TestIsNumber:

    def test_is_number_string(self) -> None:
        assert is_number("123") is True
        assert is_number("12.34") is True
        assert is_number("-5") is True
        assert is_number("hello") is False
        assert is_number("") is False

    def test_is_number_actual_numbers(self) -> None:
        assert is_number(123) is True
        assert is_number(12.34) is True
        assert is_number(-5) is True

    def test_is_number_other_types(self) -> None:
        assert is_number(None) is False
        assert is_number([]) is False


class TestPrepareLikePattern:

    def test_no_pattern(self) -> None:
        pattern_found, result = prepare_like_pattern_value("hello")
        assert pattern_found is False
        assert result == "hello"

    def test_star_pattern(self) -> None:
        pattern_found, result = prepare_like_pattern_value("hello*")
        assert pattern_found is True
        assert result == "hello%"

    def test_multiple_stars(self) -> None:
        pattern_found, result = prepare_like_pattern_value("*hello*world*")
        assert pattern_found is True
        assert result == "%hello%world%"

    def test_escaped_star(self) -> None:
        pattern_found, result = prepare_like_pattern_value("hello\\*world")
        assert pattern_found is False
        assert result == "hello\\*world"

    def test_percent_escaping(self) -> None:
        pattern_found, result = prepare_like_pattern_value("hello%world")
        assert pattern_found is True
        assert result == "hello\\%world"


class TestExpressionToSQL:

    def test_string_equals(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("message"), Operator.EQUALS.value, "hello", True)
        result = expression_to_sql(expr, fields)
        assert result == "`message` = 'hello'"

    def test_string_not_equals(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("message"), Operator.NOT_EQUALS.value, "hello", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`message` != 'hello'"

    def test_string_regex(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("message"), Operator.REGEX.value, "test.*", True)
        result = expression_to_sql(expr, fields)
        assert result == "regexp(`message`, 'test.*')"

    def test_string_not_regex(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("message"), Operator.NOT_REGEX.value, "test.*", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "not regexp(`message`, 'test.*')"

    def test_int_comparison(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("count"), Operator.GREATER_THAN.value, 10, False)
        result = expression_to_sql(expr, fields)
        assert result == "`count` > 10"

    def test_float_comparison(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("price"), Operator.LOWER_THAN.value, 99.99, False)
        result = expression_to_sql(expr, fields)
        assert result == "`price` < 99.99"

    def test_bool_equals(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("active"), Operator.EQUALS.value, True, False)
        result = expression_to_sql(expr, fields)
        assert result == "`active` = '1'"

    def test_like_pattern(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("message"), Operator.EQUALS.value, "hello*", True)
        result = expression_to_sql(expr, fields)
        assert result == "`message` LIKE 'hello%'"

    def test_not_like_pattern(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("message"), Operator.NOT_EQUALS.value, "hello*", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`message` NOT LIKE 'hello%'"

    def test_unknown_field(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("unknown_field"), Operator.EQUALS.value, "test", True
        )
        with pytest.raises(FlyqlError, match="unknown column"):
            expression_to_sql(expr, fields)

    def test_forbidden_operation(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("count"), Operator.REGEX.value, "test", True)
        with pytest.raises(FlyqlError, match="operation not allowed"):
            sql = expression_to_sql(expr, fields)
            print(sql)


class TestNewJSONColumns:

    def test_json_field_simple_path(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.name"), Operator.EQUALS.value, "test", True
        )
        result = expression_to_sql(expr, fields)
        expected = "`new_json`->'name' = 'test'"
        assert result == expected

    def test_json_field_nested_path(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.user.name"), Operator.EQUALS.value, "john", True
        )
        result = expression_to_sql(expr, fields)
        expected = "`new_json`->'user'->'name' = 'john'"
        assert result == expected

    def test_json_field_number_value(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("new_json.age"), Operator.EQUALS.value, 25, False)
        result = expression_to_sql(expr, fields)
        expected = "`new_json`->'age' = 25"
        assert result == expected

    def test_json_field_underscore_in_name(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.field_name"), Operator.EQUALS.value, "test", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`new_json`->'field_name' = 'test'"

    def test_json_field_hyphen_in_name(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.field-name"), Operator.EQUALS.value, "test", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`new_json`->'field-name' = 'test'"

    def test_json_field_starting_with_underscore(
        self, fields: dict[str, Column]
    ) -> None:
        expr = Expression(
            parse_key("new_json._private"), Operator.EQUALS.value, "test", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`new_json`->'_private' = 'test'"


class TestJSONColumnValidationErrors:

    def test_json_field_with_quotes(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.'field\"with\"quotes'"),
            Operator.EQUALS.value,
            "test",
            True,
        )
        with pytest.raises(FlyqlError, match="Invalid JSON path part"):
            expression_to_sql(expr, fields)

    def test_json_field_with_spaces(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.field with spaces"), Operator.EQUALS.value, "test", True
        )
        with pytest.raises(FlyqlError, match="Invalid JSON path part"):
            expression_to_sql(expr, fields)

    def test_json_field_with_special_chars(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.field@special"), Operator.EQUALS.value, "test", True
        )
        with pytest.raises(FlyqlError, match="Invalid JSON path part"):
            expression_to_sql(expr, fields)

    def test_json_field_starting_with_digit(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.123field"), Operator.EQUALS.value, "test", True
        )
        with pytest.raises(FlyqlError, match="Invalid JSON path part"):
            expression_to_sql(expr, fields)

    def test_json_field_starting_with_hyphen(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.-invalid"), Operator.EQUALS.value, "test", True
        )
        with pytest.raises(FlyqlError, match="Invalid JSON path part"):
            expression_to_sql(expr, fields)

    def test_json_field_empty_path_part(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("new_json.user..field"), Operator.EQUALS.value, "test", True
        )
        with pytest.raises(FlyqlError, match="Invalid JSON path part"):
            expression_to_sql(expr, fields)


class TestJSONColumns:

    def test_json_field_string_extraction(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("json_field.name"), Operator.EQUALS.value, "test", True
        )
        result = expression_to_sql(expr, fields)
        expected = "parse_json(`json_field`)->'name' = 'test'"
        assert result == expected

    def test_json_field_nested_path(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("json_field.user.name"), Operator.EQUALS.value, "john", True
        )
        result = expression_to_sql(expr, fields)
        expected = "parse_json(`json_field`)->'user'->'name' = 'john'"
        assert result == expected

    def test_json_field_number_value(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("json_field.age"), Operator.EQUALS.value, 25, False)
        result = expression_to_sql(expr, fields)
        expected = "parse_json(`json_field`)->'age' = 25"
        assert result == expected


class TestMapColumns:

    def test_map_field_access(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("metadata.key1"), Operator.EQUALS.value, "value1", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`metadata`['key1'] = 'value1'"

    def test_map_field_nested_key(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("metadata.nested.key"), Operator.EQUALS.value, "value", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`metadata`['nested']['key'] = 'value'"


class TestArrayColumns:

    def test_array_field_access(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("tags.0"), Operator.EQUALS.value, "tag1", True)
        result = expression_to_sql(expr, fields)
        assert result == "`tags`[0] = 'tag1'"

    def test_array_field_invalid_index(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("tags.invalid"), Operator.EQUALS.value, "tag1", True
        )
        with pytest.raises(FlyqlError, match="invalid array index"):
            expression_to_sql(expr, fields)


class TestStructColumns:

    def test_struct_field_access(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("user_info.name"), Operator.EQUALS.value, "value1", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`user_info`.'name' = 'value1'"

    def test_struct_field_nested_key(self, fields: dict[str, Column]) -> None:
        expr = Expression(
            parse_key("user_info.nested.name"), Operator.EQUALS.value, "value", True
        )
        result = expression_to_sql(expr, fields)
        assert result == "`user_info`.'nested'.'name' = 'value'"


class TestTreeToSQL:

    def test_simple_expression(self, fields: dict[str, Column]) -> None:
        expr = Expression(parse_key("message"), Operator.EQUALS.value, "hello", True)
        node = Node("", expr, None, None)
        result = to_sql(node, fields)
        assert result == "`message` = 'hello'"

    def test_and_operation(self, fields: dict[str, Column]) -> None:
        left_expr = Expression(
            parse_key("message"), Operator.EQUALS.value, "hello", True
        )
        right_expr = Expression(
            parse_key("count"), Operator.GREATER_THAN.value, 10, False
        )

        left_node = Node("", left_expr, None, None)
        right_node = Node("", right_expr, None, None)
        root_node = Node("and", None, left_node, right_node)

        result = to_sql(root_node, fields)
        assert result == "(`message` = 'hello' and `count` > 10)"

    def test_or_operation(self, fields: dict[str, Column]) -> None:
        left_expr = Expression(
            parse_key("message"), Operator.EQUALS.value, "hello", True
        )
        right_expr = Expression(
            parse_key("message"), Operator.EQUALS.value, "world", True
        )

        left_node = Node("", left_expr, None, None)
        right_node = Node("", right_expr, None, None)
        root_node = Node("or", None, left_node, right_node)

        result = to_sql(root_node, fields)
        assert result == "(`message` = 'hello' or `message` = 'world')"

    def test_complex_tree(self, fields: dict[str, Column]) -> None:
        expr1 = Expression(parse_key("message"), Operator.EQUALS.value, "hello", True)
        expr2 = Expression(parse_key("count"), Operator.GREATER_THAN.value, 10, False)
        expr3 = Expression(parse_key("active"), Operator.EQUALS.value, True, False)

        node1 = Node("", expr1, None, None)
        node2 = Node("", expr2, None, None)
        node3 = Node("", expr3, None, None)

        and_node = Node("and", None, node1, node2)
        root_node = Node("or", None, and_node, node3)

        result = to_sql(root_node, fields)
        assert result == "((`message` = 'hello' and `count` > 10) or `active` = '1')"


@pytest.mark.parametrize(
    "field_name,operator,value,value_is_string,expected",
    [
        ("message", Operator.EQUALS.value, "test", True, "`message` = 'test'"),
        ("count", Operator.NOT_EQUALS.value, 42, False, "`count` != '42'"),
        (
            "price",
            Operator.GREATER_OR_EQUALS_THAN.value,
            10.5,
            False,
            "`price` >= 10.5",
        ),
        ("active", Operator.EQUALS.value, True, False, "`active` = '1'"),
        (
            "created_at",
            Operator.LOWER_OR_EQUALS_THAN.value,
            "2023-01-01",
            True,
            "`created_at` <= '2023-01-01'",
        ),
    ],
)
def test_various_field_operations(
    fields: dict[str, Column],
    field_name: str,
    operator: str,
    value: str,
    value_is_string: bool,
    expected: str,
) -> None:
    expr = Expression(parse_key(field_name), operator, value, value_is_string)
    result = expression_to_sql(expr, fields)
    assert result == expected
