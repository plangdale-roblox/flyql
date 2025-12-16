NORMALIZED_TYPE_STRING = "string"
NORMALIZED_TYPE_INT = "int"
NORMALIZED_TYPE_FLOAT = "float"
NORMALIZED_TYPE_BOOL = "bool"
NORMALIZED_TYPE_DATE = "date"
NORMALIZED_TYPE_ARRAY = "array"
NORMALIZED_TYPE_MAP = "map"
NORMALIZED_TYPE_STRUCT = "struct"
NORMALIZED_TYPE_SPECIAL = "special"
NORMALIZED_TYPE_JSON = "json"

NORMALIZED_TYPE_TO_STARROCKS_TYPES = {
    NORMALIZED_TYPE_STRING: {
        "string",
        "varchar",
        "char",
        "binary",
        "varbinary",
    },
    NORMALIZED_TYPE_INT: {
        "int",
        "tinyint",
        "smallint",
        "largeint",
        "bigint",
    },
    NORMALIZED_TYPE_FLOAT: {
        "float",
        "double",
        "decimal",
    },
    NORMALIZED_TYPE_BOOL: {"bool", "boolean"},
    NORMALIZED_TYPE_DATE: {
        "date",
        "datetime",
    },
    NORMALIZED_TYPE_SPECIAL: {"bitmap", "hll"},
    NORMALIZED_TYPE_JSON: {"json"},
}
