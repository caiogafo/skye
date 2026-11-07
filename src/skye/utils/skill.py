"""The Claude Code skill that ships with the package, and the code that installs it.

The skill follows the official layout of a Claude skill: a short ``SKILL.md`` that says what to do
first and which reference to
read, and a ``references/`` folder with one small file per topic (command line, language, router,
flow, prompt, Python API,
rules). A model loads ``SKILL.md`` when the skill triggers and opens a reference only when the task
needs it. ``evals/`` holds
the test prompts and expectations of the skill (``evals.json``) and the trigger queries
(``trigger_evals.json``); like the
official packager, the installer does **not** copy ``evals/``.

``skye skill install`` copies the skill to the folder where Claude Code looks for skills:
``~/.claude/skills/skye/`` (scope
``user``) or ``./.claude/skills/skye/`` (scope ``project``), and records what it wrote in
``.skye-skill.json`` (the package version
and a hash of each file). That record is how the skill stays current on the user's machine:

* a skill that was installed and not edited is replaced by the new one on the next ``skye skill
  install`` (no ``--force``);
* a file the user edited is never replaced without ``--force``;
* ``skye skill status`` says whether the installed skill is up to date, outdated (the package
  changed) or edited.

**Whoever changes the command line, the grammar, the public API or the rules must update the
matching file in the same change**
(tests check that the files cover every command, option, field, keyword and public function, and
that their ``skye`` examples
pass ``skye check``).
"""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from skye.base.exceptions import ConfigurationError

SKILL_NAME = "skye"
SCOPES = ("user", "project")

#: The folders copied next to ``SKILL.md`` (the official ones that a skill ships; ``evals/`` stays
#: in the repository).
SHIPPED_DIRS = ("references", "scripts", "assets")

#: The record the installer writes next to ``SKILL.md``: the package version and the hash of every
#: file it wrote.
MANIFEST = ".skye-skill.json"


def _root() -> Traversable:
    return resources.files("skye.utils").joinpath("claude_skill", SKILL_NAME)


def _walk(node: Traversable, prefix: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for child in sorted(node.iterdir(), key=lambda c: c.name):
        name = f"{prefix}{child.name}"
        if child.is_dir():
            if child.name != "__pycache__":
                found.update(_walk(child, f"{name}/"))
        else:
            found[name] = child.read_text(encoding="utf-8")
    return found


def digest(text: str) -> str:
    """The SHA-256 of a text, as hexadecimal."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def package_version() -> str:
    """The version of the package that ships this skill."""
    import skye

    return str(getattr(skye, "__version__", "unknown"))


def skill_text() -> str:
    """The text of ``SKILL.md`` that ships with this version of the package."""
    return _root().joinpath("SKILL.md").read_text(encoding="utf-8")


def skill_files() -> dict[str, str]:
    """Every file the installer copies, by path relative to the skill folder (``SKILL.md``,
    ``references/...``).
    """
    root = _root()
    files = {"SKILL.md": skill_text()}
    for folder in SHIPPED_DIRS:
        node = root.joinpath(folder)
        if node.is_dir():
            files.update(_walk(node, f"{folder}/"))
    return files


def reference_names() -> list[str]:
    """The names of the reference files (``cli``, ``language``, ... for ``references/cli.md``)."""
    return sorted(
        Path(name).stem
        for name in skill_files()
        if name.startswith("references/") and name.endswith(".md")
    )


def reference_text(name: str) -> str:
    """The text of ``references/<name>.md``.

    Raises:
        ConfigurationError: If there is no such reference (the message lists the names).
    """
    files = skill_files()
    key = f"references/{name}.md"
    if key not in files:
        raise ConfigurationError(
            f'no reference "{name}". References: {", ".join(reference_names())}',
            details={"name": name},
        )
    return files[key]


def skills_dir(scope: str = "user", directory: str | Path | None = None) -> Path:
    """The folder that holds the skills.

    Args:
        scope: ``"user"`` for ``~/.claude/skills`` or ``"project"`` for ``./.claude/skills``.
        directory: A skills folder to use instead (the skill goes in ``directory/skye/``).

    Raises:
        ConfigurationError: If ``scope`` is not ``user`` or ``project``.
    """
    if directory is not None:
        return Path(directory)
    if scope == "user":
        return Path.home() / ".claude" / "skills"
    if scope == "project":
        return Path.cwd() / ".claude" / "skills"
    raise ConfigurationError(
        f'unknown scope "{scope}"; use user or project', details={"scope": scope}
    )


def skill_path(scope: str = "user", directory: str | Path | None = None) -> Path:
    """The file where ``SKILL.md`` is (or would be) installed."""
    return skills_dir(scope, directory) / SKILL_NAME / "SKILL.md"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigurationError(f"Cannot read {path}: {exc}", details={"path": str(path)}) from exc


def _manifest(base: Path) -> dict[str, object] | None:
    path = base / MANIFEST
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _recorded(base: Path) -> dict[str, str]:
    files = (_manifest(base) or {}).get("files")
    return {k: v for k, v in files.items() if isinstance(v, str)} if isinstance(files, dict) else {}


def _inspect(base: Path) -> tuple[str, list[str], dict[str, str]]:
    """The state of an installed skill, the files that were edited, and the files that exist.

    States: ``not installed``, ``up to date``, ``outdated`` (every file is as the installer wrote
        it, but the package has
    changed) and ``edited`` (some file differs both from the package and from what the installer
    wrote).
    """
    files = skill_files()
    present = {
        name: _read(base / name) for name in {*files, *_recorded(base)} if (base / name).is_file()
    }
    if "SKILL.md" not in present:
        return "not installed", [], present
    recorded = _recorded(base)
    edited = sorted(
        name
        for name, text in present.items()
        if (name not in files or text != files[name]) and recorded.get(name) != digest(text)
    )
    if edited:
        return "edited", edited, present
    if (
        all(present.get(name) == text for name, text in files.items())
        and not (set(recorded) - set(files))
        and ((_manifest(base) or {}).get("version") == package_version())
    ):
        return "up to date", [], present
    return "outdated", [], present


def skill_status(scope: str = "user", directory: str | Path | None = None) -> tuple[str, str]:
    """Whether the installed skill is current: a state and a sentence for the user.

    The states are ``"not installed"``, ``"up to date"``, ``"outdated"`` (the package changed since
    it was installed: run
    ``skye skill install``) and ``"edited"`` (a file was changed by hand: ``skye skill install
    --force`` replaces it).
    """
    base = skills_dir(scope, directory) / SKILL_NAME
    state, edited, _ = _inspect(base)
    if state == "not installed":
        return state, f"not installed ({base}); run: skye skill install"
    if state == "up to date":
        return state, f"up to date ({base}, skyeai {package_version()})"
    if state == "outdated":
        installed = (_manifest(base) or {}).get("version", "unknown")
        return (
            state,
            f"outdated (installed from skyeai {installed}, this is {package_version()}); run: "
            f"skye skill install",
        )
    return (
        state,
        f"edited by hand ({', '.join(edited)}); run: skye skill install --force to replace it",
    )


def install_skill(
    scope: str = "user",
    directory: str | Path | None = None,
    *,
    force: bool = False,
) -> tuple[Path, str]:
    """Copy the skill (``SKILL.md`` and ``references/``) to the folder where Claude Code reads
    skills.

    A skill that was installed by this command and not edited is updated without ``force``; a file
    edited by hand is not
    replaced unless ``force`` is set. Files that an older version wrote and this one no longer has
    are removed if they were not
    edited. The record ``.skye-skill.json`` is written with the version and the hash of each file.

    Args:
        scope: ``"user"`` or ``"project"`` (see :func:`skills_dir`).
        directory: A skills folder to use instead of the scope's.
        force: Replace files that were edited by hand.

    Returns:
        The path of ``SKILL.md`` and a status: ``"installed"`` (new), ``"up to date"`` or
        ``"updated"``.

    Raises:
        ConfigurationError: If a file was edited by hand and ``force`` is not set, or a file cannot
            be written.
    """
    base = skills_dir(scope, directory) / SKILL_NAME
    files = skill_files()
    state, edited, present = _inspect(base)
    if state == "edited" and not force:
        raise ConfigurationError(
            f"{base / edited[0]} was edited and differs from this version of the skill"
            f"{f' (and {len(edited) - 1} more)' if len(edited) > 1 else ''}; use --force to "
            f"replace it",
            details={"path": str(base / edited[0]), "files": edited},
        )
    if state == "up to date":
        return base / "SKILL.md", "up to date"
    stale = sorted(set(_recorded(base)) - set(files))
    try:
        for name, text in files.items():
            if present.get(name) == text:
                continue
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        for name in stale:
            if name in present and (force or digest(present[name]) == _recorded(base).get(name)):
                (base / name).unlink()
        record = {
            "package": "skyeai",
            "version": package_version(),
            "files": {n: digest(t) for n, t in files.items()},
        }
        (base / MANIFEST).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Cannot write {base}: {exc}", details={"path": str(base)}
        ) from exc
    return base / "SKILL.md", "installed" if state == "not installed" else "updated"


__all__ = [
    "MANIFEST",
    "SCOPES",
    "SHIPPED_DIRS",
    "SKILL_NAME",
    "digest",
    "install_skill",
    "package_version",
    "reference_names",
    "reference_text",
    "skill_files",
    "skill_path",
    "skill_status",
    "skill_text",
    "skills_dir",
]
