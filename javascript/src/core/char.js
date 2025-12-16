import {
    AT,
    DELIMITER,
    DOT,
    UNDERSCORE,
    COLON,
    SLASH,
    HYPHEN,
    BACKSLASH,
    BRACKET_OPEN,
    BRACKET_CLOSE,
    EQUAL_SIGN,
    EXCL_MARK,
    TILDE,
    LOWER_THAN,
    GREATER_THAN,
    DOUBLE_QUOTE,
    SINGLE_QUOTE,
    NEWLINE,
    VALID_BOOL_OPERATORS_CHARS,
} from './constants.js'

export class Char {
    constructor(value, pos, line, linePos) {
        this.value = value
        this.pos = pos
        this.line = line
        this.linePos = linePos
    }

    isDelimiter() {
        return this.value === DELIMITER
    }

    isKey() {
        return (
            /^[a-zA-Z0-9]$/.test(this.value) ||
            this.value === UNDERSCORE ||
            this.value === DOT ||
            this.value === COLON ||
            this.value === SLASH ||
            this.value === HYPHEN ||
            this.value === AT
        )
    }

    isOp() {
        return (
            this.value === EQUAL_SIGN ||
            this.value === EXCL_MARK ||
            this.value === TILDE ||
            this.value === LOWER_THAN ||
            this.value === GREATER_THAN
        )
    }

    isGroupOpen() {
        return this.value === BRACKET_OPEN
    }

    isGroupClose() {
        return this.value === BRACKET_CLOSE
    }

    isDoubleQuote() {
        return this.value === DOUBLE_QUOTE
    }

    isDoubleQuotedValue() {
        return !this.isDoubleQuote()
    }

    isSingleQuote() {
        return this.value === SINGLE_QUOTE
    }

    isSingleQuotedValue() {
        return !this.isSingleQuote()
    }

    isBackslash() {
        return this.value === BACKSLASH
    }

    isEquals() {
        return this.value === EQUAL_SIGN
    }

    isValue() {
        return (
            !this.isDoubleQuote() &&
            !this.isSingleQuote() &&
            !this.isDelimiter() &&
            !this.isGroupOpen() &&
            !this.isGroupClose() &&
            !this.isEquals()
        )
    }

    isNewline() {
        return this.value === NEWLINE
    }

    isBoolOpChar() {
        return VALID_BOOL_OPERATORS_CHARS.includes(this.value)
    }
}
