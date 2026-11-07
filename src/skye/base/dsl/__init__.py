"""The ``.skye`` language: parser, checker, expression checker and block models (decisions D50 to
D61).

The functions take text, never a path: ``base`` does no file I/O. The code that reads a file
(``skye check``, the component that loads a router or a flow) reads the text and calls them.

Entry points:

* :func:`parse` ``(text, filename=None) -> Tree``: the syntax tree; raises :class:`SkyeSyntaxError`
  with every syntax mistake found.
* :func:`build` ``(text_or_tree, *, filename=None, registry_names=None) -> Document``: the validated
  blocks (``RouterSpec``, ``FlowSpec``, ``PromptSpec``) and the list of diagnostics.
* :func:`check_text` ``(text, filename=None, registry_names=None) -> list[Diagnostic]``.
* :func:`block_schema` ``(kind=None) -> dict``: the JSON Schema of the blocks.
* :func:`evaluate` ``(expression, scope)``: a safe evaluator (never ``eval``).
* :func:`skeleton` ``(kind, name=None, template=None) -> str``: a starting ``.skye`` text.

Codename: stratus.
"""

from skye.base.dsl.build import Document, build, check_text
from skye.base.dsl.cache import CacheInfo, build_cached, cache_info, clear_cache
from skye.base.dsl.emit import to_text
from skye.base.dsl.errors import Diagnostic, SkyeSyntaxError, did_you_mean, suggest
from skye.base.dsl.expressions import (
    ALLOWED_FUNCTIONS,
    Expression,
    SkyeExpressionError,
    check_expression,
    evaluate,
)
from skye.base.dsl.lexer import Token, tokenize
from skye.base.dsl.parser import parse, parse_collect
from skye.base.dsl.schema import block_schema
from skye.base.dsl.skeletons import TEMPLATES, new_flow, new_prompt, new_router, skeleton
from skye.base.dsl.specs import (
    AllowedFailsPolicySpec,
    BranchSpec,
    ChoiceSpec,
    ContextFieldSpec,
    ContextSpec,
    FlowSpec,
    ParallelSpec,
    PromptPartSpec,
    PromptSpec,
    RetryPolicySpec,
    RetrySpec,
    RouterSpec,
    RouteSpec,
    SetSpec,
    StepSpec,
    TargetSpec,
    VariableSpec,
    format_duration,
    parse_duration,
)
from skye.base.dsl.tree import Tree

__all__ = [
    "ALLOWED_FUNCTIONS",
    "TEMPLATES",
    "AllowedFailsPolicySpec",
    "BranchSpec",
    "CacheInfo",
    "ChoiceSpec",
    "ContextFieldSpec",
    "ContextSpec",
    "Diagnostic",
    "Document",
    "Expression",
    "FlowSpec",
    "ParallelSpec",
    "PromptPartSpec",
    "PromptSpec",
    "RetryPolicySpec",
    "RetrySpec",
    "RouteSpec",
    "RouterSpec",
    "SetSpec",
    "SkyeExpressionError",
    "SkyeSyntaxError",
    "StepSpec",
    "TargetSpec",
    "Token",
    "Tree",
    "VariableSpec",
    "block_schema",
    "build",
    "build_cached",
    "cache_info",
    "check_expression",
    "check_text",
    "clear_cache",
    "did_you_mean",
    "evaluate",
    "format_duration",
    "new_flow",
    "new_prompt",
    "new_router",
    "parse",
    "parse_collect",
    "parse_duration",
    "skeleton",
    "suggest",
    "to_text",
    "tokenize",
]
