"""The lexer of the ``.skye`` language: text in, tokens with line and column out.

Tokens carry their start and end offsets so that an expression can be kept as the exact text
of the file. ``#`` comments are dropped. A newline is a token (it ends an attribute).
"""

from __future__ import annotations

from dataclasses import dataclass

from skye.base.dsl.errors import Diagnostic

IDENT = "ident"
STRING = "string"
NUMBER = "number"
PUNCT = "punct"
OP = "op"
NEWLINE = "newline"
EOF = "eof"

_PUNCT = frozenset("{}[](),=.:")
_TWO_CHAR_OPS = frozenset({"==", "!=", "<=", ">=", "//", "**"})
_ONE_CHAR_OPS = frozenset("<>+-*/%|&^~!")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


@dataclass(frozen=True, kw_only=True)
class Token:
    """One token.

    Attributes:
        kind: ``ident``, ``string``, ``number``, ``punct``, ``op``, ``newline`` or ``eof``.
        text: The source text of the token.
        value: The decoded value (the content of a string, the number of a number token).
        line: The line, counted from 1.
        column: The column, counted from 1.
        start: The offset of the first character in the text.
        end: The offset after the last character.
    """

    kind: str
    text: str
    value: str | int | float | None
    line: int
    column: int
    start: int
    end: int


def _decode(raw: str) -> str:
    """Process the escapes of a string body (an unknown escape is kept as written)."""
    if "\\" not in raw:
        return raw
    out: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            if nxt in _ESCAPES:
                out.append(_ESCAPES[nxt])
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _dedent(raw: str) -> str:
    """The body of a ``\"\"\"`` string: first newline dropped, common indentation removed."""
    if raw.startswith("\n"):
        raw = raw[1:]
    elif raw.startswith("\r\n"):
        raw = raw[2:]
    lines = raw.split("\n")
    indents = [len(x) - len(x.lstrip()) for x in lines[:-1] if x.strip()]
    last = lines[-1]
    if last.strip():
        indents.append(len(last) - len(last.lstrip()))
    margin = min(indents) if indents else 0
    stripped = [x[margin:] if x.strip() else x.lstrip(" \t") for x in lines]
    if stripped and not stripped[-1].strip():  # the closing quotes sit on their own line
        stripped[-1] = ""
        return "\n".join(stripped[:-1]) if len(stripped) > 1 else ""
    return "\n".join(stripped)


def tokenize(text: str, filename: str) -> tuple[list[Token], list[Diagnostic]]:
    """Split ``text`` into tokens.

    Args:
        text: The ``.skye`` text.
        filename: The name used in the diagnostics.

    Returns:
        The tokens (ending with an ``eof`` token) and the mistakes found (an unterminated
        string, a character that is not part of the language, a malformed number).
    """
    tokens: list[Token] = []
    errors: list[Diagnostic] = []
    n = len(text)
    i = 0
    line = 1
    line_start = 0

    def fail(at: int, row: int, start_of_line: int, reason: str, fix: str = "") -> None:
        errors.append(
            Diagnostic(
                file=filename, line=row, column=at - start_of_line + 1, reason=reason, fix=fix
            )
        )

    def add(kind: str, start: int, end: int, value: str | int | float | None = None) -> None:
        tokens.append(
            Token(
                kind=kind,
                text=text[start:end],
                value=value,
                line=line,
                column=start - line_start + 1,
                start=start,
                end=end,
            )
        )

    while i < n:
        ch = text[i]
        if ch == "\n":
            add(NEWLINE, i, i + 1)
            i += 1
            line += 1
            line_start = i
        elif ch in " \t\r":
            i += 1
        elif ch == "#":
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith('"""', i):
            close = text.find('"""', i + 3)
            while close != -1 and text[close - 1] == "\\":
                close = text.find('"""', close + 1)
            if close == -1:
                fail(i, line, line_start, 'unterminated """ string', 'Add the closing """')
                break
            body = text[i + 3 : close]
            add(STRING, i, close + 3, _decode(_dedent(body)))
            newlines = text.count("\n", i, close + 3)
            if newlines:
                line += newlines
                line_start = text.rfind("\n", i, close + 3) + 1
            i = close + 3
        elif ch == '"':
            j = i + 1
            while j < n and text[j] not in '"\n':
                j += 2 if text[j] == "\\" and j + 1 < n and text[j + 1] != "\n" else 1
            if j >= n or text[j] != '"':
                fail(i, line, line_start, "unterminated string", 'Add the closing quote (")')
                while j < n and text[j] != "\n":
                    j += 1
                i = j
                continue
            add(STRING, i, j + 1, _decode(text[i + 1 : j]))
            i = j + 1
        elif ch.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            is_float = False
            if j + 1 < n and text[j] == "." and text[j + 1].isdigit():
                is_float = True
                j += 1
                while j < n and text[j].isdigit():
                    j += 1
            if j < n and text[j] in "eE":
                k = j + 1
                if k < n and text[k] in "+-":
                    k += 1
                if k < n and text[k].isdigit():
                    is_float = True
                    while k < n and text[k].isdigit():
                        k += 1
                    j = k
            if j < n and (text[j].isalpha() or text[j] == "_"):
                end = j
                while end < n and (text[end].isalnum() or text[end] == "_"):
                    end += 1
                fail(
                    i,
                    line,
                    line_start,
                    f'"{text[i:end]}" is not a valid number',
                    'A duration is a string with a unit: "30s", "5m" or "24h".',
                )
                i = end
                continue
            literal = text[i:j]
            add(NUMBER, i, j, float(literal) if is_float else int(literal))
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            add(IDENT, i, j, text[i:j])
            i = j
        elif text[i : i + 2] in _TWO_CHAR_OPS:
            add(OP, i, i + 2)
            i += 2
        elif ch in _PUNCT:
            add(PUNCT, i, i + 1)
            i += 1
        elif ch in _ONE_CHAR_OPS:
            add(OP, i, i + 1)
            i += 1
        else:
            fail(i, line, line_start, f"unexpected character {ch!r}")
            i += 1
    tokens.append(
        Token(kind=EOF, text="", value=None, line=line, column=n - line_start + 1, start=n, end=n)
    )
    return tokens, errors
