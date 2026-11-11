"""MkDocs hook: syntax highlighting for ``skye`` code blocks (decision D103).

A small Pygments lexer for the ``.skye`` language, built from the same keyword lists as the VS Code grammar
(``src/skye/utils/vscode_extension/syntaxes/skye.tmLanguage.json``). It lives with the docs, not in the package: the library ships
no Pygments dependency. The hook makes ``pymdownx.highlight`` find it under the names ``skye`` and ``.skye``.
"""

from __future__ import annotations

from typing import Any

from pygments.lexer import RegexLexer, bygroups, words
from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String, Text, Whitespace

BLOCKS = (
    "router", "flow", "prompt", "route", "target", "retry_policy", "allowed_fails_policy", "step", "parallel", "choice",
    "context", "message", "placeholder", "output", "each", "when", "else",
)
STATEMENTS = ("set", "emit", "in", "end")
LOGICAL = ("and", "or", "not", "is", "if")
TYPES = ("string", "number", "bool", "list", "map")
FUNCTIONS = ("len", "min", "max", "abs", "round", "str", "int", "float")
CONSTANTS = ("true", "false", "none", "True", "False", "None")
REFERENCES = ("registry", "flow", "router", "prompt", "env", "context", "step", "item", "loop")


class SkyeLexer(RegexLexer):
    """Lexer for the ``.skye`` language of Skye."""

    name = "Skye"
    aliases = ["skye", ".skye"]
    filenames = ["*.skye"]

    tokens = {
        "root": [
            (r"\s+", Whitespace),
            (r"#.*?$", Comment.Single),
            (r"/\*", Comment.Multiline, "comment"),
            (r'"""', String.Double, "triple"),
            (r'"(\d+(?:\.\d+)?[smhd])"', String.Other),
            (r'"', String.Double, "string"),
            (r"'(?:[^'\\]|\\.)*'", String.Single),
            (r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b", Number),
            (words(CONSTANTS, prefix=r"\b", suffix=r"\b"), Keyword.Constant),
            (r"\b(" + "|".join(REFERENCES) + r")(\.)", bygroups(Name.Builtin, Punctuation)),
            (words(BLOCKS, prefix=r"\b", suffix=r"\b(?!\s*=(?!=))"), Keyword),
            (words(STATEMENTS, prefix=r"\b", suffix=r"\b"), Keyword.Reserved),
            (words(LOGICAL, prefix=r"\b", suffix=r"\b"), Operator.Word),
            (words(TYPES, prefix=r"\b", suffix=r"\b"), Keyword.Type),
            (words(FUNCTIONS, prefix=r"\b", suffix=r"(?=\s*\()"), Name.Function),
            (r"\b([A-Za-z_][A-Za-z0-9_]*)(\s*)(?==(?!=))", bygroups(Name.Attribute, Text)),
            (r"==|!=|<=|>=|<|>|//|\*\*|[+\-*/%]|=|[|&^~!]", Operator),
            (r"[{}\[\](),:.]", Punctuation),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name),
        ],
        "comment": [
            (r"[^*]+", Comment.Multiline),
            (r"\*/", Comment.Multiline, "#pop"),
            (r"\*", Comment.Multiline),
        ],
        "string": [
            (r'\\[ntr"\\]', String.Escape),
            (r"\{\{", String.Interpol, "interpolation"),
            (r'"', String.Double, "#pop"),
            (r'[^"\\{]+', String.Double),
            (r"[\\{]", String.Double),
        ],
        "triple": [
            (r"\{\{", String.Interpol, "interpolation"),
            (r'"""', String.Double, "#pop"),
            (r'[^"{]+', String.Double),
            (r'["{]', String.Double),
        ],
        "interpolation": [
            (r"\}\}", String.Interpol, "#pop"),
            (r"\|\s*[A-Za-z_][A-Za-z0-9_]*", Name.Function),
            (r"[^}|]+", Name.Variable),
            (r"[}|]", Name.Variable),
        ],
    }


def on_config(config: Any) -> Any:
    """Let ``pymdownx.highlight`` resolve ``skye`` to :class:`SkyeLexer`."""
    import pymdownx.highlight as highlight

    original = highlight.get_lexer_by_name
    if getattr(original, "_skye", False):
        return config

    def get_lexer_by_name(name: str, **options: Any) -> Any:
        if name.lower() in ("skye", ".skye"):
            return SkyeLexer(**options)
        return original(name, **options)

    get_lexer_by_name._skye = True  # type: ignore[attr-defined]
    highlight.get_lexer_by_name = get_lexer_by_name
    return config
