"""The VS Code side of the `skye` command: `check --format json` and stdin, and `skye vscode`.

No real VS Code: ``shutil.which`` and ``subprocess.run`` are patched, and folder installs go to
``tmp_path``. Most tests use a small fake extension folder; one packages the real one.
"""

from __future__ import annotations

import io
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import pytest

from skye.base.dsl import skeleton
from skye.utils import vscode
from skye.utils.cli import main

VSX = "{http://schemas.microsoft.com/developer/vsx-schema/2011}"
TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"
GOOD = skeleton("prompt", "hello", None)
BAD = "router r {\n  bogus: 1\n}\n"


@pytest.fixture
def fake_extension(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "ext_src"
    (root / "syntaxes").mkdir(parents=True)
    package = {
        "name": "skye",
        "publisher": "skyeai",
        "displayName": "Skye",
        "description": "Skye & .skye <files>",
        "version": "0.0.0",
        "engines": {"vscode": "^1.75.0"},
    }
    (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
    (root / "extension.js").write_text("exports.activate = () => {};\n", encoding="utf-8")
    (root / "README.md").write_text("# Skye\n", encoding="utf-8")
    (root / "LICENSE.txt").write_text("MIT\n", encoding="utf-8")
    (root / "syntaxes" / "skye.tmLanguage.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(vscode, "_root", lambda: root)
    monkeypatch.setattr(vscode, "extension_version", lambda: "1.2.3")
    return root


@pytest.fixture
def no_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vscode.shutil, "which", lambda name: None)


# -- skye check: --format json and stdin ---------------------------------------------------------


def _stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(text))


def test_check_json_from_stdin_valid(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stdin(monkeypatch, GOOD)
    assert main(["check", "--format", "json", "-"]) == 0
    assert json.loads(capsys.readouterr().out) == {"diagnostics": []}


def test_check_json_from_stdin_invalid_uses_the_stdin_filename(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stdin(monkeypatch, BAD)
    assert main(["check", "--format", "json", "--stdin-filename", "a.skye", "-"]) == 1
    out = capsys.readouterr().out
    data = json.loads(out)  # exactly one JSON object
    assert out.count("\n") == 1 and data["diagnostics"]
    first = data["diagnostics"][0]
    assert set(first) == {"file", "line", "column", "reason", "fix", "message"}
    assert first["file"] == "a.skye" and first["line"] == 2 and first["column"] >= 1
    assert first["message"].startswith(first["reason"])


def test_check_text_from_stdin_default_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stdin(monkeypatch, GOOD)
    assert main(["check", "-"]) == 0
    assert capsys.readouterr().out == "<stdin>: ok\n"
    _stdin(monkeypatch, BAD)
    assert main(["check", "-"]) == 1
    assert capsys.readouterr().out.startswith("<stdin>:2:")


def test_check_json_files_and_read_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good, bad = tmp_path / "good.skye", tmp_path / "bad.skye"
    good.write_text(GOOD, encoding="utf-8")
    bad.write_text(BAD, encoding="utf-8")
    assert main(["check", "--format", "json", str(good), str(bad)]) == 1
    files = {d["file"] for d in json.loads(capsys.readouterr().out)["diagnostics"]}
    assert files == {str(bad)}
    assert main(["check", "--format", "json", str(bad), str(tmp_path / "missing.skye")]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "cannot read" in captured.err


# -- the .vsix -------------------------------------------------------------------------------------


def test_version_is_plain_semver(monkeypatch: pytest.MonkeyPatch) -> None:
    for raw, expected in (("0.1.0.dev3", "0.1.0"), ("2.0", "2.0.0"), ("1.4.2rc1", "1.4.2")):
        monkeypatch.setattr(vscode.metadata, "version", lambda name, raw=raw: raw)
        assert vscode.extension_version() == expected

    def missing(name: str) -> str:
        raise vscode.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(vscode.metadata, "version", missing)
    import skye

    assert vscode.extension_version() == skye.__version__


def _check_vsix(path: Path, version: str, files: set[str]) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert names == {"extension.vsixmanifest", "[Content_Types].xml"} | {
            f"extension/{f}" for f in files
        }
        package = json.loads(archive.read("extension/package.json"))
        manifest = ElementTree.fromstring(archive.read("extension.vsixmanifest"))
        types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
    assert package["version"] == version
    identity = manifest.find(f"{VSX}Metadata/{VSX}Identity")
    assert identity is not None
    assert (identity.get("Id"), identity.get("Publisher"), identity.get("Version")) == (
        "skye",
        "skyeai",
        version,
    )
    target = manifest.find(f"{VSX}Installation/{VSX}InstallationTarget")
    assert target is not None and target.get("Id") == "Microsoft.VisualStudio.Code"
    props = {p.get("Id"): p.get("Value") for p in manifest.iter(f"{VSX}Property")}
    assert props["Microsoft.VisualStudio.Code.Engine"] == package["engines"]["vscode"]
    assets = {a.get("Type"): a.get("Path") for a in manifest.iter(f"{VSX}Asset")}
    assert assets["Microsoft.VisualStudio.Code.Manifest"] == "extension/package.json"
    assert assets["Microsoft.VisualStudio.Services.Content.License"] == "extension/LICENSE.txt"
    license_tag = manifest.find(f"{VSX}Metadata/{VSX}License")
    assert license_tag is not None and license_tag.text == "extension/LICENSE.txt"
    extensions = {d.get("Extension") for d in types.iter(f"{TYPES}Default")}
    assert {".json", ".js", ".md", ".txt", ".vsixmanifest", ".xml"} <= extensions
    return package


def test_package_builds_the_vsix(
    fake_extension: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "out.vsix"
    assert main(["vscode", "package", "-o", str(out)]) == 0
    assert capsys.readouterr().out.strip() == str(out)
    files = {"package.json", "extension.js", "README.md", "LICENSE.txt"}
    package = _check_vsix(out, "1.2.3", files | {"syntaxes/skye.tmLanguage.json"})
    assert package["description"] == "Skye & .skye <files>"  # escaped in the XML, kept in JSON
    monkeypatch.chdir(tmp_path)
    assert main(["vscode", "package"]) == 0
    assert (tmp_path / "skye-1.2.3.vsix").is_file()


def test_package_the_real_extension(tmp_path: Path) -> None:
    root = vscode._root()
    assert root.is_dir(), "src/skye/utils/vscode_extension is missing"
    files = set(vscode.extension_files())
    assert {"package.json", "extension.js", "LICENSE.txt"} <= files
    out = vscode.build_vsix(tmp_path / "real.vsix")
    package = _check_vsix(out, vscode.extension_version(), files)
    assert (package["name"], package["publisher"]) == ("skye", "skyeai")
    assert out.stat().st_size < 100_000


# -- install through the editor ------------------------------------------------------------------


def _fake_run(calls: list[list[str]], stdout: str = "", returncode: int = 0) -> Any:
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert "shell" not in kwargs and kwargs["timeout"] == 120
        calls.append(list(command))
        if "--install-extension" in command:
            assert zipfile.is_zipfile(command[2])  # the .vsix exists while the editor runs
        return subprocess.CompletedProcess(command, returncode, stdout, "boom")

    return run


def test_install_with_the_first_editor_found(
    fake_extension: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    looked: list[str] = []

    def which(name: str) -> str | None:
        looked.append(name)
        return "/bin/codium" if name == "codium" else None

    calls: list[list[str]] = []
    monkeypatch.setattr(vscode.shutil, "which", which)
    monkeypatch.setattr(vscode.subprocess, "run", _fake_run(calls))
    assert main(["vscode", "install"]) == 0
    assert looked == ["code", "code-insiders", "codium"]
    assert calls[0][0] == "/bin/codium" and calls[0][1] == "--install-extension"
    assert calls[0][2].endswith("skye-1.2.3.vsix") and calls[0][3] == "--force"
    out = capsys.readouterr().out
    assert "skyeai.skye@1.2.3" in out and "skye.command" in out


def test_install_with_a_given_editor_and_failures(
    fake_extension: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(vscode.shutil, "which", lambda n: f"/x/{n}" if n == "cursor" else None)
    monkeypatch.setattr(vscode.subprocess, "run", _fake_run(calls, returncode=1))
    assert main(["vscode", "install", "--editor", "cursor"]) == 2
    assert calls[0][0] == "/x/cursor" and "boom" in capsys.readouterr().err
    assert main(["vscode", "install", "--editor", "nope"]) == 2
    assert "cannot find" in capsys.readouterr().err


def test_editor_status_and_uninstall(
    fake_extension: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(vscode.shutil, "which", lambda n: "/bin/code" if n == "code" else None)
    for listing, code, word in (
        ("ms-python.python@1.0.0\nskyeai.skye@1.2.3\n", 0, "up to date"),
        ("skyeai.skye@1.0.0\n", 1, "outdated"),
        ("ms-python.python@1.0.0\n", 1, "not installed"),
    ):
        monkeypatch.setattr(vscode.subprocess, "run", _fake_run(calls, stdout=listing))
        assert main(["vscode", "status"]) == code
        assert capsys.readouterr().out.startswith(word)
    assert calls[-1] == ["/bin/code", "--list-extensions", "--show-versions"]
    assert main(["vscode", "uninstall"]) == 0
    assert calls[-1] == ["/bin/code", "--uninstall-extension", "skyeai.skye"]


# -- install by copying the folder ---------------------------------------------------------------


def test_folder_install_when_no_editor_is_found(
    fake_extension: Path,
    no_editor: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(vscode.Path, "home", lambda: tmp_path / "home")
    assert main(["vscode", "install"]) == 0
    target = tmp_path / "home" / ".vscode" / "extensions" / "skyeai.skye-1.2.3"
    out = capsys.readouterr().out
    assert f"installed: {target}" in out and "reload VS Code" in out and "skye.command" in out
    assert json.loads((target / "package.json").read_text())["version"] == "1.2.3"
    assert main(["vscode", "path"]) == 0
    assert capsys.readouterr().out.strip() == str(target)


def test_folder_install_manifest_status_and_edits(
    fake_extension: Path, no_editor: None, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exts = tmp_path / "exts"
    assert main(["vscode", "status", "--dir", str(exts)]) == 1
    assert capsys.readouterr().out.startswith("not installed")

    assert main(["vscode", "install", "--dir", str(exts)]) == 0
    target = exts / "skyeai.skye-1.2.3"
    record = json.loads((target / vscode.MANIFEST).read_text())
    assert record["version"] == "1.2.3"
    assert set(record["files"]) == set(vscode.extension_files())
    assert main(["vscode", "status", "--dir", str(exts)]) == 0
    assert capsys.readouterr().out.count("up to date") == 1
    assert main(["vscode", "install", "--dir", str(exts)]) == 0
    assert capsys.readouterr().out.startswith("up to date")

    # the package changed: the files are as the installer wrote them, so it is only outdated
    (fake_extension / "extension.js").write_text("exports.activate = () => 1;\n")
    assert main(["vscode", "status", "--dir", str(exts)]) == 1
    assert capsys.readouterr().out.startswith("outdated")
    assert main(["vscode", "install", "--dir", str(exts)]) == 0
    assert capsys.readouterr().out.startswith("updated")

    # a file edited by hand is not replaced without --force
    (target / "README.md").write_text("mine\n")
    assert main(["vscode", "status", "--dir", str(exts)]) == 1
    assert "edited by hand (README.md)" in capsys.readouterr().out
    assert main(["vscode", "install", "--dir", str(exts)]) == 2
    assert "--force" in capsys.readouterr().err
    assert (target / "README.md").read_text() == "mine\n"
    assert main(["vscode", "install", "--dir", str(exts), "--force"]) == 0
    assert (target / "README.md").read_text() == "# Skye\n"


def test_folder_install_replaces_an_older_version(
    fake_extension: Path, no_editor: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exts = tmp_path / "exts"
    monkeypatch.setattr(vscode, "extension_version", lambda: "1.0.0")
    vscode.install_extension(directory=exts)
    monkeypatch.setattr(vscode, "extension_version", lambda: "1.2.3")
    assert vscode.extension_status(directory=exts)[0] == "outdated"
    vscode.install_extension(directory=exts)
    assert sorted(p.name for p in exts.iterdir()) == ["skyeai.skye-1.2.3"]


def test_folder_uninstall_removes_only_our_folders(
    fake_extension: Path, no_editor: None, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exts = tmp_path / "exts"
    (exts / "skyeai.skye-0.9.0").mkdir(parents=True)  # not ours: no record
    assert main(["vscode", "uninstall", "--dir", str(exts)]) == 0
    assert capsys.readouterr().out.startswith("not installed")
    assert main(["vscode", "install", "--dir", str(exts)]) == 0
    assert main(["vscode", "uninstall", "--dir", str(exts)]) == 0
    assert "removed" in capsys.readouterr().out
    assert sorted(p.name for p in exts.iterdir()) == ["skyeai.skye-0.9.0"]
