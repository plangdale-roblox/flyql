import re
from typing import List, Optional

from flyql.generators.clickhouse.constants import (
    NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES,
    NORMALIZED_TYPE_STRING,
    NORMALIZED_TYPE_INT,
    NORMALIZED_TYPE_FLOAT,
    NORMALIZED_TYPE_BOOL,
    NORMALIZED_TYPE_DATE,
    NORMALIZED_TYPE_ARRAY,
    NORMALIZED_TYPE_MAP,
    NORMALIZED_TYPE_TUPLE,
    NORMALIZED_TYPE_GEOMETRY,
    NORMALIZED_TYPE_INTERVAL,
    NORMALIZED_TYPE_SPECIAL,
    NORMALIZED_TYPE_JSON,
)

REGEX = {
    "wrapper": re.compile(
        r"^(nullable|lowcardinality|simpleaggregatefunction|aggregatefunction)\s*\(\s*(.+)\s*\)"
    ),
    NORMALIZED_TYPE_STRING: re.compile(r"^(varchar|char|fixedstring)\s*\(\s*\d+\s*\)"),
    NORMALIZED_TYPE_INT: re.compile(
        r"^(tinyint|smallint|mediumint|int|integer|bigint)\s*\(\s*\d+\s*\)"
    ),
    NORMALIZED_TYPE_FLOAT: re.compile(
        r"^(decimal|numeric|dec)\d*\s*\(\s*\d+\s*(,\s*\d+)?\s*\)"
    ),
    NORMALIZED_TYPE_DATE: re.compile(r"^datetime64\s*\(\s*\d+\s*(,\s*.+)?\s*\)"),
    NORMALIZED_TYPE_ARRAY: re.compile(r"^array\s*\("),
    NORMALIZED_TYPE_MAP: re.compile(r"^map\s*\("),
    NORMALIZED_TYPE_TUPLE: re.compile(r"^tuple\s*\("),
    NORMALIZED_TYPE_JSON: re.compile(r"^json\s*\("),
}


def normalize_clickhouse_type(ch_type: str) -> Optional[str]:
    if not ch_type or not isinstance(ch_type, str):
        return None

    normalized = ch_type.strip().lower()

    match = REGEX["wrapper"].match(normalized)
    if match:
        normalized = match.group(2).strip()

    if REGEX[NORMALIZED_TYPE_STRING].match(normalized):
        return NORMALIZED_TYPE_STRING

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_STRING]:
        return NORMALIZED_TYPE_STRING

    if REGEX[NORMALIZED_TYPE_INT].match(normalized):
        return NORMALIZED_TYPE_INT

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_INT]:
        return NORMALIZED_TYPE_INT

    if REGEX[NORMALIZED_TYPE_FLOAT].match(normalized):
        return NORMALIZED_TYPE_FLOAT

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_FLOAT]:
        return NORMALIZED_TYPE_FLOAT

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_BOOL]:
        return NORMALIZED_TYPE_BOOL

    if REGEX[NORMALIZED_TYPE_DATE].match(normalized):
        return NORMALIZED_TYPE_DATE

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_DATE]:
        return NORMALIZED_TYPE_DATE

    if REGEX[NORMALIZED_TYPE_JSON].match(normalized):
        return NORMALIZED_TYPE_JSON

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_JSON]:
        return NORMALIZED_TYPE_JSON

    if REGEX[NORMALIZED_TYPE_ARRAY].match(normalized):
        return NORMALIZED_TYPE_ARRAY

    if REGEX[NORMALIZED_TYPE_MAP].match(normalized):
        return NORMALIZED_TYPE_MAP

    if REGEX[NORMALIZED_TYPE_TUPLE].match(normalized):
        return NORMALIZED_TYPE_TUPLE

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_GEOMETRY]:
        return NORMALIZED_TYPE_GEOMETRY

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_INTERVAL]:
        return NORMALIZED_TYPE_INTERVAL

    if normalized in NORMALIZED_TYPE_TO_CLICKHOUSE_TYPES[NORMALIZED_TYPE_SPECIAL]:
        return NORMALIZED_TYPE_SPECIAL

    return None


class Field:
    def __init__(
        self,
        name: str,
        jsonstring: bool,
        _type: str,
        values: Optional[List[str]] = None,
    ):
        self.name = name
        self.jsonstring = jsonstring
        self.type = _type
        self.values = values or []
        self.normalized_type = normalize_clickhouse_type(_type)
        self.is_map = self.normalized_type == NORMALIZED_TYPE_MAP
        self.is_array = self.normalized_type == NORMALIZED_TYPE_ARRAY
        self.is_json = self.normalized_type == NORMALIZED_TYPE_JSON
