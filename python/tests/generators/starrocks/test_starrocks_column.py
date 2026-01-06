import pytest
from flyql.generators.starrocks.column import Column, normalize_starrocks_type


@pytest.mark.parametrize(
    "input_type,expected",
    [
        ("String", "string"),
        ("VARCHAR(255)", "string"),
        ("CHAR(10)", "string"),
        ("TINYINT", "int"),
        ("BIGINT(20)", "int"),
        ("Decimal(10,2)", "float"),
        ("Bool", "bool"),
        ("Boolean", "bool"),
        ("DateTime", "date"),
        ("Array<String>", "array"),
        ("Map<String, Int>", "map"),
        ("Bitmap", "special"),
        ("UnknownType", None),
        ("", None),
    ],
)
def test_normalize_starrocks_type(input_type: str, expected: str) -> None:
    result = normalize_starrocks_type(input_type)
    assert result == expected


class TestField:

    def test_field_creation_basic(self) -> None:
        field = Column("test_field", False, "String")
        assert field.name == "test_field"
        assert field.jsonstring is False
        assert field.type == "String"
        assert field.values == []
        assert field.normalized_type == "string"
        assert field.is_map is False
        assert field.is_array is False

    def test_field_creation_with_values(self) -> None:
        values = ["value1", "value2"]
        field = Column("enum_field", False, "Enum8", values)
        assert field.values == values

    def test_field_creation_map(self) -> None:
        field = Column("map_field", False, "Map<String, Int>")
        assert field.normalized_type == "map"
        assert field.is_map is True
        assert field.is_array is False

    def test_field_creation_array(self) -> None:
        field = Column("array_field", False, "Array<String>")
        assert field.normalized_type == "array"
        assert field.is_map is False
        assert field.is_array is True

    def test_field_creation_json_field(self) -> None:
        field = Column("json_field", True, "String")
        assert field.jsonstring is True
        assert field.normalized_type == "string"

    def test_field_creation_int_types(self) -> None:
        int_types = ["Int", "BIGINT", "tinyint", "SmallInt"]
        for int_type in int_types:
            field = Column("int_field", False, int_type)
            assert field.normalized_type == "int"
            assert field.is_map is False
            assert field.is_array is False

    def test_field_creation_float_types(self) -> None:
        float_types = ["float", "Decimal(10,2)", "DOUBLE"]
        for float_type in float_types:
            field = Column("float_field", False, float_type)
            assert field.normalized_type == "float"

    def test_field_creation_json(self) -> None:
        field = Column("json_field", False, "JSON")
        assert field.normalized_type == "json"
        assert field.is_json is True
        assert field.is_map is False
        assert field.is_array is False

    def test_field_creation_json_with_params(self) -> None:
        field = Column("json_field", False, "JSON(a.b UInt32)")
        assert field.normalized_type == "json"
        assert field.is_json is True

    def test_field_values_empty_list(self) -> None:
        field = Column("test", False, "String", [])
        assert field.values == []

    def test_field_creation_unknown_type(self) -> None:
        field = Column("unknown_field", False, "SomeUnknownType")
        assert field.normalized_type is None
        assert field.is_map is False
        assert field.is_array is False
        assert field.is_json is False
