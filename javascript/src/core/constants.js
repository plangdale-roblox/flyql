export const AT = '@'
export const DELIMITER = ' '
export const DOT = '.'
export const UNDERSCORE = '_'
export const COLON = ':'
export const SLASH = '/'
export const HYPHEN = '-'
export const BACKSLASH = '\\'
export const BRACKET_OPEN = '('
export const BRACKET_CLOSE = ')'
export const EQUAL_SIGN = '='
export const EXCL_MARK = '!'
export const TILDE = '~'
export const LOWER_THAN = '<'
export const GREATER_THAN = '>'
export const DOUBLE_QUOTE = '"'
export const SINGLE_QUOTE = "'"
export const NEWLINE = '\n'

export const CharType = Object.freeze({
    KEY: 'flyqlKey',
    VALUE: 'flyqlValue',
    OPERATOR: 'flyqlOperator',
    NUMBER: 'number',
    STRING: 'string',
    SPACE: 'space',
})

export const State = Object.freeze({
    INITIAL: 'Initial',
    ERROR: 'Error',
    KEY: 'Key',
    SINGLE_QUOTED_KEY: 'SingleQuotedKey',
    DOUBLE_QUOTED_KEY: 'DoubleQuotedKey',
    EXPECT_OPERATOR: 'ExpectOperator',
    VALUE: 'Value',
    EXPECT_VALUE: 'ExpectValue',
    SINGLE_QUOTED_VALUE: 'SingleQuotedValue',
    DOUBLE_QUOTED_VALUE: 'DoubleQuotedValue',
    KEY_VALUE_OPERATOR: 'KeyValueOperator',
    BOOL_OP_DELIMITER: 'BoolOpDelimiter',
    EXPECT_BOOL_OP: 'ExpectBoolOp',
    KEY_OR_BOOL_OP: 'KeyOrBoolOp',
    EXPECT_NOT_TARGET: 'ExpectNotTarget',
    EXPECT_IN_KEYWORD: 'ExpectInKeyword',
    EXPECT_LIST_START: 'ExpectListStart',
    EXPECT_LIST_VALUE: 'ExpectListValue',
    IN_LIST_VALUE: 'InListValue',
    IN_LIST_SINGLE_QUOTED_VALUE: 'InListSingleQuotedValue',
    IN_LIST_DOUBLE_QUOTED_VALUE: 'InListDoubleQuotedValue',
    EXPECT_LIST_COMMA_OR_END: 'ExpectListCommaOrEnd',
})

export const BoolOperator = Object.freeze({
    AND: 'and',
    OR: 'or',
})

export const Operator = Object.freeze({
    EQUALS: '=',
    NOT_EQUALS: '!=',
    REGEX: '~',
    NOT_REGEX: '!~',
    GREATER_THAN: '>',
    LOWER_THAN: '<',
    GREATER_OR_EQUALS_THAN: '>=',
    LOWER_OR_EQUALS_THAN: '<=',
    TRUTHY: 'truthy',
    IN: 'in',
    NOT_IN: 'not in',
})

export const NOT_KEYWORD = 'not'
export const IN_KEYWORD = 'in'

export const VALID_KEY_VALUE_OPERATORS = [
    Operator.EQUALS,
    Operator.NOT_EQUALS,
    Operator.REGEX,
    Operator.NOT_REGEX,
    Operator.GREATER_THAN,
    Operator.LOWER_THAN,
    Operator.GREATER_OR_EQUALS_THAN,
    Operator.LOWER_OR_EQUALS_THAN,
    Operator.IN,
    Operator.NOT_IN,
]

export const VALID_BOOL_OPERATORS = [BoolOperator.AND, BoolOperator.OR]

export const VALID_BOOL_OPERATORS_CHARS = ['a', 'n', 'd', 'o', 'r']
