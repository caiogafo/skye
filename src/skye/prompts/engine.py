"""Tiny standard-library template engine for Skye prompts.

Replaces the former Jinja2 dependency with a small, dependency-free subset that covers the
bundled ``templates/`` files and the prompts tests. Supported syntax:

* ``{{ expr }}`` output; ``{# comment #}``.
* ``{% if %}``, ``{% elif %}``, ``{% else %}``, ``{% endif %}``.
* ``{% for x in expr %}`` / ``{% for k, v in expr %}`` with optional ``{% else %}`` and
  ``{% endfor %}``; inside a loop ``loop.index``, ``loop.index0``, ``loop.first``,
  ``loop.last``, ``loop.length``.
* Whitespace control: ``{%-``/``-%}``/``{{-``/``-}}`` strip adjacent whitespace; a newline
  right after a block tag is dropped and indentation before a block tag is stripped
  (the former ``trim_blocks``/``lstrip_blocks`` behaviour).
* Expressions: names, dotted attribute / ``[key]`` access, method calls (``d.items()``),
  string / number / ``True``/``False``/``None`` literals, list literals, ``not``/``and``/``or``,
  ``== != < > <= >= in not in``, conditional ``a if cond else b`` and filters ``x | f(args)``.
* Built-in filters: join, upper, lower, title, capitalize, trim, length, default (alias d),
  string, list, first, last, int, float, replace, tojson, toxml, totable, map(attribute). Callers
  may add their own. ``tojson``, ``toxml`` and ``totable`` put DATA into a prompt as JSON, as XML
  (``{{ order | toxml("order") }}``: a map gives one element per key, a list repeated ``<item>``
  elements, the text is escaped) or as a Markdown table (``{{ rows | totable }}``: a list of maps,
  one row per map, the columns in order of first appearance, or the ones given:
  ``totable(["name", "price"])``). To ask the model to ANSWER in a format, use the ``output``
  block of a ``.skye`` prompt instead.

Undefined variables are left visible (``{{ name }}``) and are falsy, as with Jinja2's
``DebugUndefined``. No code is evaluated with ``eval``; only the grammar above is interpreted.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator, Mapping
from typing import Any

__all__ = [
    "DEFAULT_FILTERS",
    "CompiledTemplate",
    "TemplateSyntaxError",
    "Undefined",
    "compile_template",
    "render_template",
]


class TemplateSyntaxError(ValueError):
    """Raised when a template or an expression inside it cannot be parsed."""


class Undefined:
    """Placeholder for a missing variable: falsy, empty when iterated, prints as ``{{ name }}``."""

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def __str__(self) -> str:
        return "{{ " + self._name + " }}"

    __repr__ = __str__

    def __bool__(self) -> bool:
        return False

    def __iter__(self) -> Iterator[Any]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Undefined) and other._name == self._name

    def __hash__(self) -> int:
        return hash(self._name)


# ---------------------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------------------


def _default(value: Any, default: Any = "", boolean: bool = False) -> Any:
    if isinstance(value, Undefined) or (boolean and not value):
        return default
    return value


def _join(value: Any, sep: str = "") -> str:
    return str(sep).join(str(v) for v in value)


def _first(value: Any) -> Any:
    for item in value:
        return item
    return Undefined("first")


def _last(value: Any) -> Any:
    items = list(value)
    return items[-1] if items else Undefined("last")


_XML_BAD = re.compile(r"[^0-9A-Za-z_.-]")


def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _xml_tag(name: Any) -> str:
    tag = _XML_BAD.sub("_", str(name)) or "item"
    return tag if tag[0].isalpha() or tag[0] == "_" else f"_{tag}"


def _xml_scalar(value: Any) -> str:
    if value is None or isinstance(value, Undefined):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return _xml_escape(str(value))


def _xml_lines(tag: str, value: Any, depth: int, out: list[str]) -> None:
    pad = "  " * depth
    if isinstance(value, Mapping):
        out.append(f"{pad}<{tag}>")
        for key, item in value.items():
            _xml_lines(_xml_tag(key), item, depth + 1, out)
        out.append(f"{pad}</{tag}>")
    elif isinstance(value, list | tuple):
        out.append(f"{pad}<{tag}>")
        for item in value:
            _xml_lines("item", item, depth + 1, out)
        out.append(f"{pad}</{tag}>")
    else:
        out.append(f"{pad}<{tag}>{_xml_scalar(value)}</{tag}>")


def _toxml(value: Any, root: str = "data") -> str:
    """``value`` as indented XML under ``<root>``."""
    out: list[str] = []
    _xml_lines(_xml_tag(root), value, 0, out)
    return "\n".join(out)


def _cell(value: Any) -> str:
    if value is None or isinstance(value, Undefined):
        return ""
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, Mapping | list | tuple):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\r\n", " ").replace("\n", " ")


def _totable(value: Any, columns: Any = None) -> str:
    """A list of maps (or one map) as a Markdown table, one row per map."""
    rows = [value] if isinstance(value, Mapping) else list(value or ())
    rows = [r if isinstance(r, Mapping) else {"value": r} for r in rows]
    names: list[str] = [str(c) for c in columns] if columns else []
    if not names:
        for row in rows:
            names.extend(str(k) for k in row if str(k) not in names)
    if not names:
        return ""
    lines = ["| " + " | ".join(_cell(n) for n in names) + " |", "|" + "---|" * len(names)]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(n)) for n in names) + " |")
    return "\n".join(lines)


DEFAULT_FILTERS: dict[str, Callable[..., Any]] = {
    "join": _join,
    "upper": lambda v: str(v).upper(),
    "lower": lambda v: str(v).lower(),
    "title": lambda v: str(v).title(),
    "capitalize": lambda v: str(v).capitalize(),
    "trim": lambda v: str(v).strip(),
    "length": lambda v: len(v),
    "count": lambda v: len(v),
    "default": _default,
    "d": _default,
    "string": lambda v: str(v),
    "list": lambda v: list(v),
    "first": _first,
    "last": _last,
    "int": lambda v, default=0: _safe(int, v, default),
    "float": lambda v, default=0.0: _safe(float, v, default),
    "replace": lambda v, old, new: str(v).replace(str(old), str(new)),
    "tojson": lambda v: json.dumps(v, ensure_ascii=False),
    "toxml": _toxml,
    "totable": _totable,
    "map": lambda v, attribute: [_getattr(item, str(attribute)) for item in v],
}


def _safe(conv: Callable[[Any], Any], value: Any, default: Any) -> Any:
    try:
        return conv(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------------------
# Expression parsing (recursive descent over a small token stream)
# ---------------------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""\s*(?:
    (?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
    |(?P<num>\d+(?:\.\d+)?)
    |(?P<name>[A-Za-z_][A-Za-z0-9_]*)
    |(?P<op>==|!=|<=|>=|[<>|().,\[\]])
    )""",
    re.VERBOSE,
)

_KEYWORDS = {"not", "and", "or", "in", "if", "else"}
_CONSTANTS = {
    "True": True,
    "False": False,
    "true": True,
    "false": False,
    "None": None,
    "none": None,
}


def _tokenize(src: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    src = src.rstrip()
    while pos < len(src):
        m = _TOKEN_RE.match(src, pos)
        if not m or m.end() == pos:
            raise TemplateSyntaxError(f"Unexpected character in expression: {src[pos:]!r}")
        kind = m.lastgroup or ""
        tokens.append((kind, m.group(kind)))
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, src: str) -> None:
        self.src = src.strip()
        self.toks = _tokenize(self.src)
        self.i = 0
        # Root names read by the expression, in first-seen order (with repeats), and the ones that
        # are the operand of a ``default`` filter (so a missing value is expected).
        self.names: list[str] = []
        self.defaulted: set[str] = set()

    def peek(self) -> tuple[str, str] | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def next(self) -> tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise TemplateSyntaxError(f"Unexpected end of expression: {self.src!r}")
        self.i += 1
        return tok

    def accept(self, kind: str, value: str) -> bool:
        tok = self.peek()
        if tok and tok[0] == kind and tok[1] == value:
            self.i += 1
            return True
        return False

    def expect(self, kind: str, value: str) -> None:
        if not self.accept(kind, value):
            raise TemplateSyntaxError(f"Expected {value!r} in expression: {self.src!r}")

    def parse(self) -> Callable[[dict[str, Any]], Any]:
        node = self.ternary()
        if self.peek() is not None:
            token = self.toks[self.i][1]
            raise TemplateSyntaxError(f"Unexpected token {token!r} in expression: {self.src!r}")
        return node

    # --- grammar ---
    def ternary(self) -> Callable[[dict[str, Any]], Any]:
        value = self.or_()
        if self.accept("name", "if"):
            cond = self.or_()
            other = self.ternary() if self.accept("name", "else") else (lambda ctx: "")
            return lambda ctx: value(ctx) if cond(ctx) else other(ctx)
        return value

    def or_(self) -> Callable[[dict[str, Any]], Any]:
        left = self.and_()
        while self.accept("name", "or"):
            right, prev = self.and_(), left
            left = (lambda p, r: lambda ctx: p(ctx) or r(ctx))(prev, right)
        return left

    def and_(self) -> Callable[[dict[str, Any]], Any]:
        left = self.not_()
        while self.accept("name", "and"):
            right, prev = self.not_(), left
            left = (lambda p, r: lambda ctx: p(ctx) and r(ctx))(prev, right)
        return left

    def not_(self) -> Callable[[dict[str, Any]], Any]:
        if self.accept("name", "not"):
            inner = self.not_()
            return lambda ctx: not inner(ctx)
        return self.compare()

    def compare(self) -> Callable[[dict[str, Any]], Any]:
        left = self.filtered()
        while True:
            tok = self.peek()
            if tok is None:
                return left
            op: str | None = None
            if tok[0] == "op" and tok[1] in ("==", "!=", "<", ">", "<=", ">="):
                op = tok[1]
                self.i += 1
            elif tok == ("name", "in"):
                op = "in"
                self.i += 1
            elif (
                tok == ("name", "not")
                and self.i + 1 < len(self.toks)
                and self.toks[self.i + 1] == ("name", "in")
            ):
                op = "not in"
                self.i += 2
            if op is None:
                return left
            right, prev = self.filtered(), left
            left = (lambda p, r, o: lambda ctx: _compare(o, p(ctx), r(ctx)))(prev, right, op)

    def filtered(self) -> Callable[[dict[str, Any]], Any]:
        first_tok = self.peek()
        first_name = len(self.names)
        value = self.postfix()
        while self.accept("op", "|"):
            kind, fname = self.next()
            if kind != "name":
                raise TemplateSyntaxError(f"Invalid filter name in expression: {self.src!r}")
            if fname in ("default", "d") and first_tok is not None and first_tok[0] == "name":
                if len(self.names) > first_name and self.names[first_name] == first_tok[1]:
                    self.defaulted.add(first_tok[1])
            args = self.call_args() if self.accept("op", "(") else []
            value = (
                lambda v, n, a: lambda ctx: _apply_filter(ctx, n, v(ctx), [x(ctx) for x in a])
            )(value, fname, args)
        return value

    def call_args(self) -> list[Callable[[dict[str, Any]], Any]]:
        args: list[Callable[[dict[str, Any]], Any]] = []
        if self.accept("op", ")"):
            return args
        while True:
            args.append(self.ternary())
            if self.accept("op", ")"):
                return args
            self.expect("op", ",")

    def postfix(self) -> Callable[[dict[str, Any]], Any]:
        node = self.atom()
        while True:
            if self.accept("op", "."):
                kind, attr = self.next()
                if kind != "name":
                    raise TemplateSyntaxError(f"Invalid attribute in expression: {self.src!r}")
                node = (lambda n, a: lambda ctx: _getattr(n(ctx), a))(node, attr)
            elif self.accept("op", "["):
                key = self.ternary()
                self.expect("op", "]")
                node = (lambda n, k: lambda ctx: _getitem(n(ctx), k(ctx)))(node, key)
            elif self.accept("op", "("):
                args = self.call_args()
                node = (lambda n, a: lambda ctx: _call(n(ctx), [x(ctx) for x in a]))(node, args)
            else:
                return node

    def atom(self) -> Callable[[dict[str, Any]], Any]:
        kind, text = self.next()
        if kind == "str":
            value = (
                bytes(text[1:-1], "utf-8").decode("unicode_escape") if "\\" in text else text[1:-1]
            )
            return lambda ctx: value
        if kind == "num":
            number: Any = float(text) if "." in text else int(text)
            return lambda ctx: number
        if kind == "name":
            if text in _CONSTANTS:
                const = _CONSTANTS[text]
                return lambda ctx: const
            if text in _KEYWORDS:
                raise TemplateSyntaxError(
                    f"Unexpected keyword {text!r} in expression: {self.src!r}"
                )
            self.names.append(text)
            return lambda ctx: ctx[text] if text in ctx else Undefined(text)
        if (kind, text) == ("op", "("):
            inner = self.ternary()
            self.expect("op", ")")
            return inner
        if (kind, text) == ("op", "["):
            items: list[Callable[[dict[str, Any]], Any]] = []
            if not self.accept("op", "]"):
                while True:
                    items.append(self.ternary())
                    if self.accept("op", "]"):
                        break
                    self.expect("op", ",")
            return lambda ctx: [i(ctx) for i in items]
        raise TemplateSyntaxError(f"Unexpected token {text!r} in expression: {self.src!r}")


def _compare(op: str, a: Any, b: Any) -> bool:
    try:
        if op == "==":
            return bool(a == b)
        if op == "!=":
            return bool(a != b)
        if op == "<":
            return bool(a < b)
        if op == ">":
            return bool(a > b)
        if op == "<=":
            return bool(a <= b)
        if op == ">=":
            return bool(a >= b)
        if op == "in":
            return a in b
        return a not in b
    except TypeError:
        return False


def _getattr(obj: Any, name: str) -> Any:
    if isinstance(obj, Undefined):
        return Undefined(f"{obj._name}.{name}")
    if isinstance(obj, Mapping):
        # Like Jinja2: real attributes (``items``) win over keys only for non-data names.
        if name in obj:
            return obj[name]
        if not name.startswith("_") and hasattr(obj, name):
            return getattr(obj, name)
        return Undefined(name)
    if not name.startswith("_") and hasattr(obj, name):
        return getattr(obj, name)
    try:
        return obj[name]
    except (TypeError, KeyError, IndexError):
        return Undefined(name)


def _getitem(obj: Any, key: Any) -> Any:
    if isinstance(obj, Undefined):
        return Undefined(f"{obj._name}[{key!r}]")
    try:
        return obj[key]
    except (TypeError, KeyError, IndexError):
        if isinstance(key, str) and not key.startswith("_") and hasattr(obj, key):
            return getattr(obj, key)
        return Undefined(str(key))


def _call(fn: Any, args: list[Any]) -> Any:
    if isinstance(fn, Undefined):
        return fn
    if not callable(fn):
        raise TemplateSyntaxError(f"Value {fn!r} is not callable")
    return fn(*args)


def _apply_filter(ctx: dict[str, Any], name: str, value: Any, args: list[Any]) -> Any:
    filters = ctx.get("__filters__", DEFAULT_FILTERS)
    fn = filters.get(name)
    if fn is None:
        raise TemplateSyntaxError(f"Unknown filter: {name!r}")
    return fn(value, *args)


# ---------------------------------------------------------------------------------------
# Template lexing / parsing
# ---------------------------------------------------------------------------------------

_TAG_RE = re.compile(r"\{#.*?#\}|\{%.*?%\}|\{\{.*?\}\}", re.DOTALL)

# AST nodes are plain tuples: ("text", str) | ("out", expr) | ("if", [(cond, body)], else_body)
# | ("for", names, iter_expr, body, else_body)


def _lex(source: str) -> list[tuple[str, str]]:
    """Split into ``("text"|"block"|"var", payload)`` items applying whitespace control."""
    items: list[tuple[str, str]] = []
    pos = 0
    strip_next_ws = False
    trim_newline = False

    def add_text(text: str) -> None:
        nonlocal strip_next_ws, trim_newline
        if strip_next_ws:
            text = text.lstrip()
        elif trim_newline:
            text = (
                text[1:]
                if text.startswith("\n")
                else (text[2:] if text.startswith("\r\n") else text)
            )
        strip_next_ws = trim_newline = False
        if text:
            items.append(("text", text))

    for m in _TAG_RE.finditer(source):
        text = source[pos : m.start()]
        tag = m.group(0)
        pos = m.end()
        kind = "var" if tag.startswith("{{") else ("comment" if tag.startswith("{#") else "block")
        inner = tag[2:-2]
        left_strip = inner.startswith("-")
        right_strip = inner.endswith("-")
        if left_strip:
            inner = inner[1:]
        if right_strip:
            inner = inner[:-1]
        add_text(text)
        if left_strip:
            _rstrip_last_text(items)
        elif kind != "var":
            _lstrip_blocks(items, at_start=(m.start() == 0))
        if kind != "comment":
            items.append((kind, inner.strip()))
        strip_next_ws = right_strip
        trim_newline = kind != "var" and not right_strip
    add_text(source[pos:])
    # Jinja drops a single trailing newline by default.
    if items and items[-1][0] == "text" and items[-1][1].endswith("\n"):
        items[-1] = ("text", items[-1][1][:-1])
        if not items[-1][1]:
            items.pop()
    return items


def _rstrip_last_text(items: list[tuple[str, str]]) -> None:
    if items and items[-1][0] == "text":
        stripped = items[-1][1].rstrip()
        if stripped:
            items[-1] = ("text", stripped)
        else:
            items.pop()


def _lstrip_blocks(items: list[tuple[str, str]], at_start: bool) -> None:
    if not items or items[-1][0] != "text":
        return
    text = items[-1][1]
    line_start = text.rfind("\n") + 1
    if (line_start > 0 or at_start) and not text[line_start:].strip():
        text = text[:line_start]
        if text:
            items[-1] = ("text", text)
        else:
            items.pop()


class _TemplateParser:
    def __init__(self, source: str) -> None:
        self.items = _lex(source)
        self.i = 0
        # Free root names in first-seen order, and the ones read unconditionally (outside any
        # ``if`` and loop body, not through ``default``): those must be given at rendering.
        self.variables: dict[str, None] = {}
        self.required: dict[str, None] = {}
        self.scopes: list[set[str]] = []
        self.depth = 0

    def expr(self, src: str) -> Callable[[dict[str, Any]], Any]:
        """Compile one expression and record the free names it reads."""
        parser = _Parser(src)
        node = parser.parse()
        for name in parser.names:
            if any(name in scope for scope in self.scopes) or (self.scopes and name == "loop"):
                continue
            self.variables.setdefault(name, None)
            if self.depth == 0 and name not in parser.defaulted:
                self.required.setdefault(name, None)
        return node

    def parse(self) -> list[Any]:
        body, end = self.block(())
        if end is not None:
            raise TemplateSyntaxError(f"Unexpected {{% {end} %}}")
        return body

    def block(self, terminators: tuple[str, ...]) -> tuple[list[Any], str | None]:
        nodes: list[Any] = []
        while self.i < len(self.items):
            kind, payload = self.items[self.i]
            self.i += 1
            if kind == "text":
                nodes.append(("text", payload))
            elif kind == "var":
                nodes.append(("out", self.expr(payload)))
            else:
                word = payload.split(None, 1)[0] if payload else ""
                if word in terminators:
                    return nodes, payload
                if word == "if":
                    nodes.append(self.parse_if(payload))
                elif word == "for":
                    nodes.append(self.parse_for(payload))
                else:
                    raise TemplateSyntaxError(f"Unsupported or unexpected tag: {{% {payload} %}}")
        if terminators:
            raise TemplateSyntaxError(f"Missing {{% {terminators[-1]} %}}")
        return nodes, None

    def parse_if(self, head: str) -> Any:
        self.depth += 1
        try:
            return self._parse_if(head)
        finally:
            self.depth -= 1

    def _parse_if(self, head: str) -> Any:
        branches: list[tuple[Callable[[dict[str, Any]], Any], list[Any]]] = []
        else_body: list[Any] = []
        cond = self.expr(head[2:])
        while True:
            body, end = self.block(("elif", "else", "endif"))
            branches.append((cond, body))
            if end is None or end.split()[0] == "endif":
                break
            if end.split()[0] == "elif":
                cond = self.expr(end[4:])
                continue
            else_body, end2 = self.block(("endif",))
            if end2 is None:
                raise TemplateSyntaxError("Missing {% endif %}")
            break
        return ("if", branches, else_body)

    def parse_for(self, head: str) -> Any:
        m = re.match(r"for\s+(.+?)\s+in\s+(.+)$", head, re.DOTALL)
        if not m:
            raise TemplateSyntaxError(f"Invalid for tag: {{% {head} %}}")
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        if not names or not all(re.fullmatch(r"[A-Za-z_]\w*", n) for n in names):
            raise TemplateSyntaxError(f"Invalid loop variable in: {{% {head} %}}")
        iterable = self.expr(m.group(2))
        self.depth += 1
        self.scopes.append(set(names))
        try:
            body, end = self.block(("else", "endfor"))
        finally:
            self.scopes.pop()
        else_body: list[Any] = []
        try:
            if end is not None and end.split()[0] == "else":
                else_body, end = self.block(("endfor",))
        finally:
            self.depth -= 1
        if end is None:
            raise TemplateSyntaxError("Missing {% endfor %}")
        return ("for", names, iterable, body, else_body)


def _render_nodes(nodes: list[Any], ctx: dict[str, Any], out: list[str]) -> None:
    for node in nodes:
        tag = node[0]
        if tag == "text":
            out.append(node[1])
        elif tag == "out":
            out.append(str(node[1](ctx)))
        elif tag == "if":
            for cond, body in node[1]:
                if cond(ctx):
                    _render_nodes(body, ctx, out)
                    break
            else:
                _render_nodes(node[2], ctx, out)
        else:  # for
            _, names, iterable, body, else_body = node
            seq = iterable(ctx)
            items = list(seq.items()) if isinstance(seq, Mapping) else list(seq)
            if not items:
                _render_nodes(else_body, ctx, out)
                continue
            n = len(items)
            for idx, item in enumerate(items):
                inner = dict(ctx)
                if len(names) == 1:
                    inner[names[0]] = item
                else:
                    for name, value in zip(names, item):
                        inner[name] = value
                inner["loop"] = {
                    "index": idx + 1,
                    "index0": idx,
                    "first": idx == 0,
                    "last": idx == n - 1,
                    "length": n,
                }
                _render_nodes(body, inner, out)


class CompiledTemplate:
    """A parsed template: render it many times without parsing the text again.

    Attributes:
        variables: The free variable names the template reads, in first-seen order (loop
            variables inside their loop, ``loop``, constants and filter names are not included).
        required_variables: The names read unconditionally (outside any ``if`` and loop body and
            not through the ``default`` filter); a renderer may require them.
    """

    __slots__ = ("_nodes", "required_variables", "variables")

    def __init__(
        self, nodes: list[Any], variables: tuple[str, ...], required: tuple[str, ...]
    ) -> None:
        self._nodes = nodes
        self.variables = variables
        self.required_variables = required

    def render(
        self,
        variables: Mapping[str, Any],
        filters: Mapping[str, Callable[..., Any]] | None = None,
    ) -> str:
        """Render with ``variables``; ``filters`` extend the built-in filters.

        Args:
            variables: The values of the template variables (a missing one stays visible).
            filters: Extra filters by name; they win over the built-in ones.

        Returns:
            The rendered text.
        """
        ctx: dict[str, Any] = dict(variables)
        ctx["__filters__"] = {**DEFAULT_FILTERS, **filters} if filters else DEFAULT_FILTERS
        out: list[str] = []
        _render_nodes(self._nodes, ctx, out)
        return "".join(out)

    def __repr__(self) -> str:
        return f"CompiledTemplate(variables={self.variables!r})"


def compile_template(source: str) -> CompiledTemplate:
    """Parse ``source`` once into a :class:`CompiledTemplate`.

    Args:
        source: The template text.

    Returns:
        The compiled template with its free variable names.

    Raises:
        TemplateSyntaxError: If the template or an expression in it cannot be parsed.
    """
    parser = _TemplateParser(source)
    nodes = parser.parse()
    return CompiledTemplate(nodes, tuple(parser.variables), tuple(parser.required))


def render_template(
    template: str,
    variables: Mapping[str, Any],
    filters: Mapping[str, Callable[..., Any]] | None = None,
) -> str:
    """Render ``template`` with ``variables``; ``filters`` extend the built-in filters."""
    return compile_template(template).render(variables, filters)
