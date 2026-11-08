"""The VS Code extension for ``.skye`` files that ships with the package, and its installer.

The extension (``src/skye/utils/vscode_extension/``: syntax highlighting, brackets and comments, and
diagnostics from ``skye check --format json``) ships inside the wheel, so no marketplace is needed:

* ``skye vscode package`` builds a ``.vsix`` (a zip file, written with the standard library) with
  the version of the installed ``skyeai`` package;
* ``skye vscode install`` installs it through the editor's command line (``code``,
  ``code-insiders``, ``codium`` or ``cursor``, the first found), or, when no editor command is found
  or ``--dir`` is given, copies the unpacked extension to
  ``~/.vscode/extensions/skyeai.skye-<version>/`` and records what it wrote in
  ``.skye-vscode.json`` (the version and a hash of each file), like ``skye skill install``: a
  folder that was not edited is replaced without ``--force``, a file edited by hand is not;
* ``skye vscode status`` says whether the installed extension is up to date.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import subprocess
import tempfile
import zipfile
from importlib import metadata, resources
from importlib.resources.abc import Traversable
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from skye.base.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

#: The publisher and the name of the extension: its identifier is ``skyeai.skye``.
PUBLISHER = "skyeai"
NAME = "skye"
EXTENSION_ID = f"{PUBLISHER}.{NAME}"

#: The editor commands tried, in this order, when ``--editor`` is not given.
EDITORS = ("code", "code-insiders", "codium", "cursor")

#: The record written in an extension folder installed by copy.
MANIFEST = ".skye-vscode.json"

#: How long an editor command may run, in seconds.
TIMEOUT = 120

#: The hint printed after an install: the extension runs ``skye check``.
COMMAND_HINT = (
    "The extension runs `skye check`: the `skye` command must be on PATH, or set the "
    '`skye.command` setting (for example ["uv", "run", "skye"]).'
)

_CONTENT_TYPES = {
    ".json": "application/json",
    ".js": "application/javascript",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".vsixmanifest": "text/xml",
    ".xml": "text/xml",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


def _root() -> Traversable:
    return resources.files("skye.utils").joinpath("vscode_extension")


def _walk(node: Traversable, prefix: str) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    for child in sorted(node.iterdir(), key=lambda c: c.name):
        name = f"{prefix}{child.name}"
        if child.is_dir():
            if child.name not in ("__pycache__", "node_modules"):
                found.update(_walk(child, f"{name}/"))
        elif child.name != MANIFEST:
            found[name] = child.read_bytes()
    return found


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extension_version() -> str:
    """The version of the extension: the installed ``skyeai`` version, as ``MAJOR.MINOR.PATCH``.

    VS Code needs a plain semantic version, so a Python version such as ``0.1.0.dev3`` becomes
    ``0.1.0``; without an installed distribution the version of the ``skye`` package is used, and
    ``0.0.0`` when there is none.
    """
    try:
        raw = metadata.version("skyeai")
    except metadata.PackageNotFoundError:
        import skye

        raw = str(getattr(skye, "__version__", "0.0.0"))
    match = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", raw)
    if match is None:
        return "0.0.0"
    return ".".join(str(int(part or 0)) for part in match.groups())


def _package_json(data: bytes, version: str) -> tuple[bytes, dict[str, object]]:
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ConfigurationError(
            f"The package.json of the extension is not valid JSON: {exc}"
        ) from exc
    if not isinstance(manifest, dict):
        raise ConfigurationError("The package.json of the extension is not a JSON object")
    manifest["version"] = version
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    return text.encode("utf-8"), manifest


def extension_files(version: str | None = None) -> dict[str, bytes]:
    """Every file of the extension, by path relative to its folder, with the version filled in.

    Args:
        version: The version written in ``package.json`` (:func:`extension_version` by default).

    Raises:
        ConfigurationError: If the extension is missing from the package or its ``package.json``
            is not valid.
    """
    root = _root()
    if not root.is_dir():
        raise ConfigurationError(
            "The VS Code extension is not in this installation of skyeai",
            details={"path": str(root)},
        )
    files = _walk(root, "")
    if "package.json" not in files:
        raise ConfigurationError("The VS Code extension has no package.json")
    files["package.json"], _ = _package_json(files["package.json"], version or extension_version())
    return files


def _vsixmanifest(manifest: dict[str, object], version: str, files: dict[str, bytes]) -> str:
    engines = manifest.get("engines")
    engine = engines.get("vscode", "*") if isinstance(engines, dict) else "*"
    categories = manifest.get("categories")
    keywords = manifest.get("keywords")
    display = str(manifest.get("displayName") or manifest.get("name") or NAME)
    description = str(manifest.get("description") or "")
    assets = [
        ("Microsoft.VisualStudio.Code.Manifest", "extension/package.json"),
    ]
    license_tag = ""
    if "README.md" in files:
        assets.append(("Microsoft.VisualStudio.Services.Content.Details", "extension/README.md"))
    if "LICENSE.txt" in files:
        assets.append(("Microsoft.VisualStudio.Services.Content.License", "extension/LICENSE.txt"))
        license_tag = "\n    <License>extension/LICENSE.txt</License>"
    properties = [
        ("Microsoft.VisualStudio.Code.Engine", str(engine)),
        ("Microsoft.VisualStudio.Code.ExtensionDependencies", ""),
        ("Microsoft.VisualStudio.Code.ExtensionPack", ""),
        ("Microsoft.VisualStudio.Code.ExtensionKind", "workspace"),
        ("Microsoft.VisualStudio.Code.LocalizedLanguages", ""),
        ("Microsoft.VisualStudio.Services.GitHubFlavoredMarkdown", "true"),
        ("Microsoft.VisualStudio.Services.Content.Pricing", "Free"),
    ]
    prop_xml = "\n".join(
        f"      <Property Id={quoteattr(k)} Value={quoteattr(v)} />" for k, v in properties
    )
    asset_xml = "\n".join(
        f'    <Asset Type={quoteattr(t)} Path={quoteattr(p)} Addressable="true" />'
        for t, p in assets
    )
    tags = ",".join(str(k) for k in keywords) if isinstance(keywords, list) else ""
    cats = ",".join(str(c) for c in categories) if isinstance(categories, list) else ""
    publisher = str(manifest.get("publisher") or PUBLISHER)
    name = str(manifest.get("name") or NAME)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" \
xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id={quoteattr(name)} Version={quoteattr(version)} \
Publisher={quoteattr(publisher)} />
    <DisplayName>{escape(display)}</DisplayName>
    <Description xml:space="preserve">{escape(description)}</Description>
    <Tags>{escape(tags)}</Tags>
    <Categories>{escape(cats)}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
{prop_xml}
    </Properties>{license_tag}
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
{asset_xml}
  </Assets>
</PackageManifest>
"""


def _content_types(names: list[str]) -> str:
    found = {".json", ".js", ".md", ".txt", ".vsixmanifest", ".xml"}
    found.update(Path(n).suffix.lower() for n in names if Path(n).suffix)
    defaults = "".join(
        f"<Default Extension={quoteattr(ext)} "
        f"ContentType={quoteattr(_CONTENT_TYPES.get(ext, 'application/octet-stream'))}/>"
        for ext in sorted(found)
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        f"{defaults}</Types>\n"
    )


def default_vsix_name(version: str | None = None) -> str:
    """The default file name of the package: ``skye-<version>.vsix``."""
    return f"{NAME}-{version or extension_version()}.vsix"


def build_vsix(output: str | Path | None = None) -> Path:
    """Build the ``.vsix`` of the extension.

    The archive holds ``extension.vsixmanifest``, ``[Content_Types].xml`` and every file of the
    extension under ``extension/``, with the version of ``package.json`` set to
    :func:`extension_version`.

    Args:
        output: The file to write (``./skye-<version>.vsix`` by default).

    Returns:
        The path of the file written.

    Raises:
        ConfigurationError: If the extension is missing or the file cannot be written.
    """
    version = extension_version()
    files = extension_files(version)
    manifest = json.loads(files["package.json"].decode("utf-8"))
    target = Path(output) if output is not None else Path.cwd() / default_vsix_name(version)
    names = [f"extension/{name}" for name in files]
    try:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("extension.vsixmanifest", _vsixmanifest(manifest, version, files))
            archive.writestr("[Content_Types].xml", _content_types(names))
            for name, data in files.items():
                archive.writestr(f"extension/{name}", data)
    except OSError as exc:
        raise ConfigurationError(
            f"Cannot write {target}: {exc}", details={"path": str(target)}
        ) from exc
    logger.info("vscode extension packaged", extra={"path": str(target), "version": version})
    return target


# -- the editor's command line -------------------------------------------------------------------


def find_editor(editor: str | None = None) -> str | None:
    """The path of the editor command: ``editor`` if given, else the first of :data:`EDITORS` found.

    Raises:
        ConfigurationError: If ``editor`` is given and cannot be found.
    """
    if editor is not None:
        found = shutil.which(editor)
        if found is None:
            raise ConfigurationError(
                f'cannot find the editor command "{editor}"', details={"editor": editor}
            )
        return found
    for name in EDITORS:
        found = shutil.which(name)
        if found is not None:
            return found
    return None


def _run(command: list[str]) -> str:
    logger.info("running the editor command", extra={"command": command})
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ConfigurationError(
            f"{' '.join(command)} failed: {exc}", details={"command": command}
        ) from exc
    if done.returncode != 0:
        detail = (done.stderr or done.stdout or "").strip()
        raise ConfigurationError(
            f"{' '.join(command)} failed (exit {done.returncode}){': ' + detail if detail else ''}",
            details={"command": command, "returncode": done.returncode},
        )
    return done.stdout or ""


def _editor_version(editor: str) -> str | None:
    out = _run([editor, "--list-extensions", "--show-versions"])
    for line in out.splitlines():
        ident, _, version = line.strip().partition("@")
        if ident.lower() == EXTENSION_ID:
            return version
    return None


# -- the folder install --------------------------------------------------------------------------


def extensions_dir(directory: str | Path | None = None) -> Path:
    """The folder that holds VS Code extensions: ``directory``, or ``~/.vscode/extensions``."""
    return Path(directory) if directory is not None else Path.home() / ".vscode" / "extensions"


def extension_path(directory: str | Path | None = None) -> Path:
    """The folder where this version of the extension is (or would be) installed by copy."""
    return extensions_dir(directory) / f"{EXTENSION_ID}-{extension_version()}"


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


def _ours(directory: str | Path | None) -> list[Path]:
    """The extension folders of any version that this command installed (they carry the record)."""
    base = extensions_dir(directory)
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.glob(f"{EXTENSION_ID}-*") if p.is_dir() and (p / MANIFEST).is_file()
    )


def _edited(base: Path, files: dict[str, bytes]) -> list[str]:
    """The files of an installed folder that differ both from ``files`` and from the record."""
    recorded = _recorded(base)
    edited = []
    for name in sorted({*files, *recorded}):
        path = base / name
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot read {path}: {exc}", details={"path": str(path)}
            ) from exc
        if data != files.get(name) and recorded.get(name) != _digest(data):
            edited.append(name)
    return edited


def _folder_state(directory: str | Path | None) -> tuple[str, Path, list[str]]:
    target = extension_path(directory)
    files = extension_files()
    if not target.is_dir():
        others = [p for p in _ours(directory) if p != target]
        return ("outdated" if others else "not installed"), (others[-1] if others else target), []
    edited = _edited(target, files)
    if edited:
        return "edited", target, edited
    same = all(
        (target / n).is_file() and (target / n).read_bytes() == data for n, data in files.items()
    )
    return ("up to date" if same else "outdated"), target, []


def _install_folder(directory: str | Path | None, force: bool) -> tuple[Path, str]:
    version = extension_version()
    files = extension_files(version)
    target = extension_path(directory)
    state, _, edited = _folder_state(directory)
    if state == "edited" and not force:
        raise ConfigurationError(
            f"{target / edited[0]} was edited and differs from this version of the extension"
            f"{f' (and {len(edited) - 1} more)' if len(edited) > 1 else ''}; use --force to "
            f"replace it",
            details={"path": str(target / edited[0]), "files": edited},
        )
    if state == "up to date":
        return target, "up to date"
    existed = target.is_dir()
    stale = sorted(set(_recorded(target)) - set(files))
    try:
        for name, data in files.items():
            path = target / name
            if path.is_file() and path.read_bytes() == data:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in stale:
            path = target / name
            if path.is_file() and (force or _digest(path.read_bytes()) == _recorded(target)[name]):
                path.unlink()
        record = {
            "package": "skyeai",
            "version": version,
            "files": {n: _digest(d) for n, d in files.items()},
        }
        (target / MANIFEST).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        for old in _ours(directory):
            if old != target and (force or not _edited(old, {})):
                shutil.rmtree(old)
    except OSError as exc:
        raise ConfigurationError(
            f"Cannot write {target}: {exc}", details={"path": str(target)}
        ) from exc
    logger.info("vscode extension copied", extra={"path": str(target), "version": version})
    return target, "updated" if existed or state == "outdated" else "installed"


# -- the commands --------------------------------------------------------------------------------


def install_extension(
    editor: str | None = None,
    directory: str | Path | None = None,
    *,
    force: bool = False,
) -> tuple[str, str]:
    """Install the extension, through the editor's command line or by copying its folder.

    Without ``directory`` the editor command (``editor``, or the first of :data:`EDITORS` found)
    installs a ``.vsix`` built in a temporary folder. With ``directory``, or when no editor command
    is found, the unpacked extension is copied to ``<directory>/skyeai.skye-<version>/`` (default
    ``~/.vscode/extensions``) with a ``.skye-vscode.json`` record.

    Args:
        editor: The editor command to use (``code``, ``codium``, ...).
        directory: An extensions folder to copy the extension into instead.
        force: Replace a copied folder whose files were edited by hand.

    Returns:
        How it was installed (``"editor"`` or ``"folder"``) and a sentence for the user.

    Raises:
        ConfigurationError: If the editor command fails or is not found, a file was edited and
            ``force`` is not set, or a file cannot be written.
    """
    command = find_editor(editor) if directory is None else None
    if command is None:
        target, status = _install_folder(directory, force)
        hint = "; reload VS Code" if status != "up to date" else ""
        return "folder", f"{status}: {target}{hint}"
    with tempfile.TemporaryDirectory() as tmp:
        vsix = build_vsix(Path(tmp) / default_vsix_name())
        _run([command, "--install-extension", str(vsix), "--force"])
    return "editor", f"installed {EXTENSION_ID}@{extension_version()} with {command}"


def uninstall_extension(editor: str | None = None, directory: str | Path | None = None) -> str:
    """Remove the extension, through the editor's command line or by removing the copied folders.

    Args:
        editor: The editor command to use.
        directory: An extensions folder; the ``skyeai.skye-*`` folders that carry the record of
            this command are removed from it.

    Returns:
        A sentence for the user.

    Raises:
        ConfigurationError: If the editor command fails or a folder cannot be removed.
    """
    command = find_editor(editor) if directory is None else None
    if command is not None:
        _run([command, "--uninstall-extension", EXTENSION_ID])
        return f"uninstalled {EXTENSION_ID} with {command}"
    removed = _ours(directory)
    for folder in removed:
        try:
            shutil.rmtree(folder)
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot remove {folder}: {exc}", details={"path": str(folder)}
            ) from exc
    if not removed:
        return f"not installed ({extensions_dir(directory)})"
    return "removed " + ", ".join(str(p) for p in removed) + "; reload VS Code"


def extension_status(
    editor: str | None = None, directory: str | Path | None = None
) -> tuple[str, str]:
    """Whether the installed extension is current: a state and a sentence for the user.

    The states are ``"not installed"``, ``"up to date"``, ``"outdated"`` and, for a copied folder,
    ``"edited"``.

    Raises:
        ConfigurationError: If the editor command fails.
    """
    version = extension_version()
    command = find_editor(editor) if directory is None else None
    if command is not None:
        installed = _editor_version(command)
        if installed is None:
            return "not installed", f"not installed in {command}; run: skye vscode install"
        if installed == version:
            return "up to date", f"up to date ({EXTENSION_ID}@{version} in {command})"
        return (
            "outdated",
            f"outdated ({EXTENSION_ID}@{installed}, this is {version}); run: skye vscode install",
        )
    state, path, edited = _folder_state(directory)
    if state == "not installed":
        return state, f"not installed ({extensions_dir(directory)}); run: skye vscode install"
    if state == "up to date":
        return state, f"up to date ({path}, {EXTENSION_ID}@{version})"
    if state == "outdated":
        return state, f"outdated ({path}, this is {version}); run: skye vscode install"
    return (
        state,
        f"edited by hand ({', '.join(edited)}); run: skye vscode install --force to replace it",
    )


__all__ = [
    "COMMAND_HINT",
    "EDITORS",
    "EXTENSION_ID",
    "MANIFEST",
    "build_vsix",
    "default_vsix_name",
    "extension_files",
    "extension_path",
    "extension_status",
    "extension_version",
    "extensions_dir",
    "find_editor",
    "install_extension",
    "uninstall_extension",
]
