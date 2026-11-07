"""The ``skye`` command line: ``skye check`` and ``skye new`` for ``.skye`` files.

This is the code that reads and writes files; the parser in ``skye.base.dsl`` takes text only.

Usage::

    skye check app.skye [more.skye ...]    # prints file:line:col message; exit 1 on errors
    skye check --schema                    # prints the JSON Schema of the router, flow, prompt
    blocks
    skye new flow my_flow --template loop -o my_flow.skye
    skye new --list                        # the kinds and their templates
    skye skill install [--scope user|project] [--dir DIR] [--force]   # the Claude Code skill that
    teaches Skye
    skye skill print [NAME] | skye skill path   # SKILL.md, or references/NAME.md; where it is
    installed
    skye skill status                      # up to date, outdated (the package changed) or edited;
    exit 1 if not up to date

Exit codes: 0 no error, 1 the checked files have errors, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from skye.base.dsl import TEMPLATES, block_schema, check_text, skeleton
from skye.base.exceptions import ConfigurationError
from skye.utils.skill import (
    SCOPES,
    install_skill,
    reference_text,
    skill_path,
    skill_status,
    skill_text,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skye", description="Tools for .skye files.")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="check .skye files and print every error")
    check.add_argument("files", nargs="*", metavar="FILE", help="the .skye files to check")
    check.add_argument("--schema", action="store_true", help="print the JSON Schema of the blocks")
    check.add_argument(
        "--registry",
        metavar="NAMES",
        help="comma-separated names the registry will hold; registry.NAME is checked against them",
    )

    new = commands.add_parser("new", help="print (or write) a starting .skye file")
    new.add_argument("kind", nargs="?", choices=sorted(TEMPLATES), help="router, flow or prompt")
    new.add_argument("name", nargs="?", help="the name of the block")
    new.add_argument("--template", "-t", help="the template (see --list)")
    new.add_argument("-o", "--output", metavar="FILE", help="write to FILE instead of stdout")
    new.add_argument("--force", action="store_true", help="overwrite FILE if it exists")
    new.add_argument("--list", action="store_true", help="list the kinds and their templates")

    skill = commands.add_parser(
        "skill", help="install or print the Claude Code skill that teaches how to use Skye"
    )
    actions = skill.add_subparsers(dest="action", required=True)
    for action, text in (
        ("install", "copy the skill to the folder where Claude Code reads skills"),
        ("print", "print the skill"),
        ("path", "print where the skill is installed"),
        ("status", "say whether the installed skill is up to date (exit 1 if it is not)"),
    ):
        sub = actions.add_parser(action, help=text)
        if action == "print":
            sub.add_argument(
                "name",
                nargs="?",
                help="a reference to print (references/NAME.md); SKILL.md when omitted",
            )
        else:
            sub.add_argument(
                "--scope",
                choices=SCOPES,
                default="user",
                help="user (~/.claude/skills) or project (./.claude/skills)",
            )
            sub.add_argument(
                "--dir", metavar="DIR", help="a skills folder to use instead of the scope's"
            )
        if action == "install":
            sub.add_argument(
                "--force",
                action="store_true",
                help="replace a skill that differs from this version",
            )
    return parser


def _check(args: argparse.Namespace) -> int:
    if args.schema:
        print(json.dumps(block_schema(), indent=2))
        if not args.files:
            return 0
    if not args.files:
        print("skye check: give at least one file, or --schema", file=sys.stderr)
        return 2
    names = [n.strip() for n in args.registry.split(",") if n.strip()] if args.registry else None
    status = 0
    for name in args.files:
        try:
            text = Path(name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{name}: cannot read the file: {exc}", file=sys.stderr)
            status = max(status, 2)
            continue
        diagnostics = check_text(text, name, names)
        for item in diagnostics:
            print(item.format())
        if diagnostics:
            status = max(status, 1) if status != 2 else 2
        else:
            print(f"{name}: ok")
    return status


def _new(args: argparse.Namespace) -> int:
    if args.list:
        for kind, templates in TEMPLATES.items():
            print(f"{kind}: {', '.join(templates)} (default: {templates[0]})")
        return 0
    if args.kind is None:
        print("skye new: give a kind (router, flow or prompt), or --list", file=sys.stderr)
        return 2
    try:
        text = skeleton(args.kind, args.name, args.template)
    except ValueError as exc:
        print(f"skye new: {exc}", file=sys.stderr)
        return 2
    if args.output is None:
        sys.stdout.write(text)
        return 0
    target = Path(args.output)
    if target.exists() and not args.force:
        print(f"skye new: {target} already exists; use --force to overwrite it", file=sys.stderr)
        return 2
    try:
        target.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"skye new: cannot write {target}: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {target}")
    return 0


def _skill(args: argparse.Namespace) -> int:
    if args.action == "print":
        try:
            sys.stdout.write(skill_text() if args.name is None else reference_text(args.name))
        except ConfigurationError as exc:
            print(f"skye skill: {exc.message}", file=sys.stderr)
            return 2
        return 0
    try:
        if args.action == "path":
            print(skill_path(args.scope, args.dir))
            return 0
        if args.action == "status":
            state, message = skill_status(args.scope, args.dir)
            print(message)
            return 0 if state == "up to date" else 1
        target, status = install_skill(args.scope, args.dir, force=args.force)
    except ConfigurationError as exc:
        print(f"skye skill: {exc.message}", file=sys.stderr)
        return 2
    print(f"{status}: {target}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``skye`` command.

    Args:
        argv: The arguments (``sys.argv[1:]`` by default).

    Returns:
        The exit code: 0 on success, 1 when a checked file has errors, 2 for a usage or file error.
    """
    args = _build_parser().parse_args(argv)
    if args.command == "check":
        return _check(args)
    if args.command == "skill":
        return _skill(args)
    return _new(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
