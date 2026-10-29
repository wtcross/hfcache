"""Actual immutable release inputs, original schema parity and copy-time refusal."""

import ast
import importlib.util
import json
import os
import shutil
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from hfcache.models import dump
from hfcache.ui_models import UiAssetManifest
from tests.fixtures.ui_examples import UI_BODIES, ui_asset_manifest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def verifier():
    spec = importlib.util.spec_from_file_location(
        "web_release_test", ROOT / "scripts/web-release.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest(verifier, root, manifest):
    body = verifier.encoded(manifest)
    (root / "manifest.json").write_bytes(body)
    return verifier.digest(body)


@pytest.fixture
def assets(verifier, tmp_path):
    root = tmp_path / "assets"
    (root / "assets").mkdir(parents=True)
    for name, body in UI_BODIES.items():
        (root / name).write_bytes(body)
    manifest = json.loads(dump(ui_asset_manifest()))
    return root, manifest, write_manifest(verifier, root, manifest)


def load(verifier, assets, **options):
    root, _, expected = assets
    return verifier.load_assets(root, expected, application_version="0.2.2", **options)


def test_original_schema_manifest_and_all_indexed_bytes_are_captured(verifier, assets):
    root, original, expected = assets
    manifest, captured = load(verifier, assets)
    assert manifest == original
    assert captured == {**UI_BODIES, "manifest.json": (root / "manifest.json").read_bytes()}
    assert dump(UiAssetManifest.model_validate(manifest)) == captured["manifest.json"]
    assert verifier.digest(captured["manifest.json"]) == expected
    (root / "assets/app-12345678.js").write_bytes(b"later change")
    assert captured["assets/app-12345678.js"] == UI_BODIES["assets/app-12345678.js"]


def test_captured_manifest_parser_has_no_filesystem_effects(verifier, assets, monkeypatch):
    root, original, expected = assets
    raw = (root / "manifest.json").read_bytes()
    for name in ("local", "read_file", "open_directory", "capture_tree"):
        monkeypatch.setattr(
            verifier, name, lambda *_args, **_kwargs: pytest.fail("pure parser accessed files")
        )
    manifest, indexed = verifier.parse_assets(raw, expected, application_version="0.2.2")
    assert manifest == original
    assert indexed == {member["path"]: member for member in original["members"]}


@pytest.mark.parametrize("name", ["index.html", "assets/app-12345678.js"])
def test_zero_byte_javascript_is_valid_but_empty_entrypoint_refuses(verifier, assets, name):
    root, manifest, _ = assets
    (root / name).write_bytes(b"")
    member = next(item for item in manifest["members"] if item["path"] == name)
    member.update(bytes=0, sha256=verifier.digest(b""))
    expected = write_manifest(verifier, root, manifest)
    if name == "index.html":
        with pytest.raises(ValidationError):
            UiAssetManifest.model_validate(manifest)
        with pytest.raises(ValueError, match="web release"):
            load(verifier, (root, manifest, expected))
    else:
        UiAssetManifest.model_validate(manifest)
        _, captured = load(verifier, (root, manifest, expected))
        assert captured[name] == b""


@pytest.mark.parametrize(
    "damage",
    [
        "null-mime",
        "mime",
        "traversal",
        "absolute",
        "double-slash",
        "backslash",
        "boolean-size",
        "boolean-schema",
        "boolean-contract",
        "unknown-field",
        "duplicate-member",
        "unsorted",
        "missing-notices",
        "oversize-member",
        "unknown-tool",
        "false-digest",
        "extra-html",
    ],
)
def test_installer_refuses_original_schema_invalid_manifests(  # noqa: PLR0912 - explicit attack variants
    verifier, assets, damage
):
    root, manifest, _ = assets
    member = next(item for item in manifest["members"] if item["path"].endswith(".js"))
    if damage == "null-mime":
        member.update(path="assets/payload.unknown", mime=None)
    elif damage == "mime":
        member["mime"] = "application/json"
    elif damage == "traversal":
        member["path"] = "assets/../escape.js"
    elif damage == "absolute":
        member["path"] = "/assets/payload.js"
    elif damage == "double-slash":
        member["path"] = "assets//payload.js"
    elif damage == "backslash":
        member["path"] = "assets/evil\\payload.js"
    elif damage == "boolean-size":
        member["bytes"] = True
    elif damage == "boolean-schema":
        manifest["schema_version"] = True
    elif damage == "boolean-contract":
        manifest["build"]["ui_contract_version"] = True
    elif damage == "unknown-field":
        manifest["shell"] = "index.html"
    elif damage == "duplicate-member":
        manifest["members"].append(dict(member))
    elif damage == "unsorted":
        manifest["members"].reverse()
    elif damage == "missing-notices":
        manifest["members"] = [
            m for m in manifest["members"] if m["path"] != "THIRD_PARTY_NOTICES.txt"
        ]
    elif damage == "oversize-member":
        member["bytes"] = verifier.MAX_MEMBER + 1
    elif damage == "unknown-tool":
        manifest["build"]["toolchain"]["npm"] = "1.0"
    elif damage == "false-digest":
        member["sha256"] = "A" * 64
    else:
        member.update(path="assets/other.html", mime="text/html")
    with pytest.raises(ValidationError):
        UiAssetManifest.model_validate(manifest)
    expected = write_manifest(verifier, root, manifest)
    with pytest.raises(ValueError, match="web release"):
        load(verifier, (root, manifest, expected))


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "empty-directory",
        "file-symlink",
        "directory-symlink",
        "hardlink",
        "fifo",
        "changed",
    ],
)
def test_actual_unindexed_aliased_special_or_changed_tree_refuses(
    verifier, assets, tmp_path, damage
):
    root, _, _ = assets
    path = root / "assets/app-12345678.js"
    if damage == "missing":
        path.unlink()
    elif damage == "extra":
        (root / "assets/unindexed.js").write_bytes(b"extra")
    elif damage == "empty-directory":
        (root / "assets/empty").mkdir()
    elif damage == "file-symlink":
        path.unlink()
        path.symlink_to(root / "index.html")
    elif damage == "directory-symlink":
        (root / "assets").rename(tmp_path / "outside")
        (root / "assets").symlink_to(tmp_path / "outside", target_is_directory=True)
    elif damage == "hardlink":
        os.link(path, tmp_path / "outside-link")
    elif damage == "fifo":
        path.unlink()
        os.mkfifo(path)
    else:
        path.write_bytes(b"X" * len(path.read_bytes()))
    with pytest.raises(ValueError, match=r"web|symlink"):
        load(verifier, assets)


@pytest.mark.parametrize(
    "options",
    [
        {"require_clean": True},
        {"source_commit": "b" * 40},
        {"wire_source_digest": "f" * 64},
        {"pnpm_lock_sha256": "f" * 64},
    ],
)
def test_explicit_release_provenance_must_match(verifier, assets, options):
    with pytest.raises(ValueError, match="web"):
        load(verifier, assets, **options)


def test_manifest_hash_and_canonical_encoding_must_match(verifier, assets):
    root, manifest, _ = assets
    with pytest.raises(ValueError, match="manifest hash"):
        load(verifier, (root, manifest, "f" * 64))
    body = json.dumps(manifest).encode()
    (root / "manifest.json").write_bytes(body)
    with pytest.raises(ValueError, match="noncanonical"):
        load(verifier, (root, manifest, verifier.digest(body)))


def test_scanning_errors_propagate_instead_of_becoming_omitted_entries(
    verifier, assets, monkeypatch
):
    def blocked(_):
        message = "blocked directory inventory"
        raise PermissionError(message)

    monkeypatch.setattr(verifier.os, "scandir", blocked)
    with pytest.raises(PermissionError, match="blocked directory inventory"):
        load(verifier, assets)


def test_implied_directory_budget_is_checked_before_tree_reads(verifier, assets, monkeypatch):
    root, manifest, _ = assets
    for number in range(700):
        manifest["members"].append(
            {
                "path": f"assets/d{number:04}/a/b/c/d/e/empty.js",
                "bytes": 0,
                "sha256": verifier.digest(b""),
                "mime": "text/javascript",
            }
        )
    manifest["members"].sort(key=lambda item: item["path"])
    UiAssetManifest.model_validate(manifest)
    expected = write_manifest(verifier, root, manifest)
    monkeypatch.setattr(
        verifier.os, "scandir", lambda _: pytest.fail("directory budget precedes scan")
    )
    with pytest.raises(ValueError, match="directory bound"):
        load(verifier, (root, manifest, expected))


@pytest.fixture
def release(verifier, assets, tmp_path):
    root, manifest, _ = assets
    source = tmp_path / "source"
    source.mkdir()
    bodies = {
        ".python-version": b"3.14.6\n",
        "LICENSE": b"MIT\n",
        "README.md": b"Fixture release\n",
        "pyproject.toml": b'[project]\nname="hfcache"\nversion="0.2.2"\n',
        "uv.lock": b"fixture locked closure\n",
        "docs/guide.md": b"Fixture guide\n",
        "examples/client.py": b"# inert fixture\n",
        "web/src/wire/contracts.json": verifier.encoded({"source_digest": "c" * 64}),
        "web/pnpm-lock.yaml": b"fixture pnpm lock\n",
        **{
            name: ("inert helper source: " + name + "\n").encode()
            for name in verifier.HELPER.values()
        },
    }
    for name, body in bodies.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    manifest["build"].update(
        source_dirty=False, pnpm_lock_sha256=verifier.digest(bodies["web/pnpm-lock.yaml"])
    )
    expected = write_manifest(verifier, root, manifest)
    output = tmp_path / "release"
    output.mkdir()
    shutil.copytree(root, output / "ui")
    (output / "host-helper").mkdir()
    for name, original in verifier.HELPER.items():
        (output / "host-helper" / name).write_bytes(bodies[original])
    (output / "wheels").mkdir()
    (output / "wheels/hfcache-0.2.2-py3-none-any.whl").write_bytes(b"inert indexed wheel fixture\n")
    files = {
        path.relative_to(output).as_posix(): verifier.digest(path.read_bytes())
        for path in output.rglob("*")
        if path.is_file()
    }
    index = {
        "schema_version": 1,
        "kind": "hfcache_web_release",
        "version": "0.2.2",
        "source_commit": manifest["build"]["source_commit"],
        "source_files": {name: verifier.digest(body) for name, body in bodies.items()},
        "files": files,
        "ui_manifest_sha256": expected,
    }
    raw = verifier.encoded(index)
    (output / "web-release.json").write_bytes(raw)
    return output, source, index, verifier.digest(raw)


def repin_index(verifier, release):
    output, source, index, _ = release
    raw = verifier.encoded(index)
    (output / "web-release.json").write_bytes(raw)
    return output, source, index, verifier.digest(raw)


def test_full_native_index_binds_original_helper_source_and_exact_shipped_tree(verifier, release):
    output, source, index, expected = release
    assert verifier.verify_native(output, expected, source) == index


@pytest.mark.parametrize(
    "name",
    [
        "src/hfcache/__init__.py",
        "src/hfcache/__main__.py",
        "packaging/systemd/hfcache-failure@.service.example",
    ],
)
def test_source_index_accepts_python_entrypoints_and_systemd_template_names(
    verifier, release, name
):
    output, source, index, _ = release
    assert verifier.relative(name).as_posix() == name
    body = b"inert indexed source regression\n"
    (source / name).write_bytes(body)
    index["source_files"][name] = verifier.digest(body)
    output, source, index, expected = repin_index(verifier, release)
    assert verifier.verify_native(output, expected, source) == index


@pytest.mark.parametrize("name", ["assets/__init__.js", "assets/failure@.js"])
def test_source_only_characters_do_not_widen_asset_path_grammar(verifier, name):
    assert verifier.relative(name).as_posix() == name
    with pytest.raises(ValueError, match="web release"):
        verifier.relative(name, asset=True)


def test_native_release_index_matches_stable_synthetic_golden(verifier, release):
    _, _, index, _ = release
    assert (
        verifier.encoded(index)
        == (ROOT / "tests/fixtures/schemas/deployment/web-release.json").read_bytes()
    )


@pytest.mark.parametrize(
    "damage", ["helper", "helper-source", "wheel", "root-source", "wire-source"]
)
def test_missing_required_closure_cannot_be_redefined_by_rehashing_index(verifier, release, damage):
    _, _, index, _ = release
    if damage == "helper":
        del index["files"]["host-helper/host_actions.py"]
    elif damage == "helper-source":
        del index["source_files"]["src/hfcache/host_actions.py"]
    elif damage == "wheel":
        del index["files"]["wheels/hfcache-0.2.2-py3-none-any.whl"]
    elif damage == "root-source":
        del index["source_files"]["LICENSE"]
    else:
        del index["source_files"]["web/src/wire/contracts.json"]
    output, source, _, expected = repin_index(verifier, release)
    with pytest.raises(ValueError, match=r"missing|extra"):
        verifier.verify_native(output, expected, source)


def test_indexed_replacement_helper_must_still_equal_original_source(verifier, release):
    output, _, index, _ = release
    replacement = b"different helper bytes\n"
    (output / "host-helper/host_actions.py").write_bytes(replacement)
    index["files"]["host-helper/host_actions.py"] = verifier.digest(replacement)
    output, source, _, expected = repin_index(verifier, release)
    with pytest.raises(ValueError, match="mismatched host helper"):
        verifier.verify_native(output, expected, source)


@pytest.mark.parametrize("damage", ["extra-file", "extra-directory", "symlink"])
def test_unindexed_shipped_source_is_refused(verifier, release, damage):
    output, source, _, expected = release
    path = source / "src/unindexed"
    if damage == "extra-file":
        path.write_bytes(b"unindexed")
    elif damage == "extra-directory":
        path.mkdir()
    else:
        path.symlink_to(source / "LICENSE")
    with pytest.raises(ValueError, match=r"extra shipped source|symlink shipped source"):
        verifier.verify_native(output, expected, source)


@pytest.mark.parametrize("folder", ["host-helper", "wheels"])
def test_unindexed_release_artifacts_are_refused(verifier, release, folder):
    output, source, _, expected = release
    (output / folder / "unindexed").write_bytes(b"unindexed")
    with pytest.raises(ValueError, match="extra release artifact"):
        verifier.verify_native(output, expected, source)


def test_native_stage_rechecks_copies_and_normalizes_modes(verifier, release, tmp_path):
    output, source, index, expected = release
    destination = tmp_path / "stage"
    shutil.copytree(source, destination)
    previous = os.umask(0o077)
    try:
        verifier.stage_native(output, destination, index, expected)
    finally:
        os.umask(previous)
    for name, wanted in index["files"].items():
        if name.startswith(("ui/", "host-helper/")):
            path = destination / name
            assert verifier.digest(path.read_bytes()) == wanted
            assert path.stat().st_mode & 0o777 == 0o644
            assert path.parent.stat().st_mode & 0o777 == 0o755
    assert verifier.digest((destination / "web-release.json").read_bytes()) == expected


@pytest.mark.parametrize("damage", ["artifact", "index", "copied-source", "existing-tree"])
def test_copy_time_changes_refuse_and_preserve_failed_stage(verifier, release, tmp_path, damage):
    output, source, index, expected = release
    verifier.verify_native(output, expected, source)
    destination = tmp_path / "stage"
    shutil.copytree(source, destination)
    if damage == "artifact":
        (output / "ui/index.html").write_bytes(b"changed after verification")
    elif damage == "index":
        (output / "web-release.json").write_bytes(b"changed after verification")
    elif damage == "copied-source":
        (destination / "src/hfcache/host_actions.py").write_bytes(b"copy changed")
    else:
        (destination / "ui").symlink_to(tmp_path / "unrelated", target_is_directory=True)
    with pytest.raises((ValueError, FileExistsError), match=r"changed|hash mismatch|File exists"):
        verifier.stage_native(output, destination, index, expected)
    assert not (destination / "web-release.json").exists()
    assert destination.is_dir()
    if damage == "copied-source":
        assert not (destination / "host-helper").exists()


def test_installer_remains_host_python312_syntax_compatible():
    ast.parse((ROOT / "scripts/web-release.py").read_text(), feature_version=(3, 12))


@pytest.fixture
def python_donor(verifier, release, tmp_path, monkeypatch):
    """Small inert tree for copy safety; installed relocation is separate acceptance."""
    output, source, index, expected = release
    root = tmp_path / "python"
    donor = root / f"cpython-3.14.6-linux-{os.uname().machine}-gnu"
    files = {
        "bin/python3.14": b"inert executable bytes\n",
        "bin/pip": b"known installer script\n",
        "bin/pip3": b"known installer script\n",
        "bin/pip3.14": b"known installer script\n",
        "lib/python3.14/os.py": b"public stdlib bytes\n",
        "lib/python3.14/_retained.py": b"public underscore member\n",
        "lib/python3.14/pip-example.py": b"retained noninstaller bytes\n",
        "lib/python3.14/ensurepip/__init__.py": b"known optional installer\n",
        "lib/python3.14/ensurepip/_bundled/pip.whl": b"inert installer bundle\n",
        "lib/python3.14/site-packages/pip/__init__.py": b"known installer\n",
        "lib/python3.14/site-packages/pip-26.1.2.dist-info/METADATA": (
            b"Metadata-Version: 2.4\nName: pip\nVersion: 26.1.2\n\n"
        ),
        "lib/libpython3.14.so.1.0": b"\x00\xff public library fixture\n",
    }
    for name, body in files.items():
        path = donor / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        path.chmod(0o755 if name.startswith("bin/") else 0o644)
    (donor / "bin/python3").symlink_to("python3.14")
    (donor / "lib/libpython3.14.so").symlink_to("libpython3.14.so.1.0")
    monkeypatch.setattr(verifier, "PYTHON_OWNER", os.geteuid())
    probes = []

    def probe(executable, version, prefix, *, managers):
        assert executable == prefix / "bin/python3.14"
        assert version == "3.14.6"
        assert bool((prefix / "lib/python3.14/site-packages/pip").exists()) == managers
        probes.append((str(executable), version, managers))

    monkeypatch.setattr(verifier, "probe_python", probe)
    return SimpleNamespace(
        root=root,
        donor=donor,
        interpreter=donor / "bin/python3.14",
        output=output,
        source=source,
        index=index,
        expected=expected,
        probes=probes,
    )


def prepare_python(verifier, fixture):
    return verifier.prepare_python(fixture.interpreter, fixture.root, fixture.source, fixture.index)


def test_native_python_copy_preserves_donor_and_omits_only_known_optional_installers(
    verifier, python_donor
):
    before = verifier.python_inventory(python_donor.donor)
    executable = prepare_python(verifier, python_donor)
    destination = executable.parent.parent
    copied, _identities = verifier.python_inventory(destination)
    assert destination.name == "web-0.2.2-" + python_donor.index["source_commit"]
    assert stat.S_IMODE(destination.stat().st_mode) == 0o755
    assert verifier.python_inventory(python_donor.donor) == before
    removed = set(before[0]) - set(copied)
    roots = {
        "bin/pip",
        "bin/pip3",
        "bin/pip3.14",
        "lib/python3.14/ensurepip",
        "lib/python3.14/site-packages/pip",
        "lib/python3.14/site-packages/pip-26.1.2.dist-info",
    }
    assert removed == {
        name
        for name in before[0]
        if any(name == item or name.startswith(item + "/") for item in roots)
    }
    assert copied == {name: row for name, row in before[0].items() if name not in removed}
    assert (
        destination / "lib/python3.14/pip-example.py"
    ).read_bytes() == b"retained noninstaller bytes\n"
    assert (destination / "bin/python3").readlink() == Path("python3.14")
    assert [row[2] for row in python_donor.probes] == [True, False]
    with pytest.raises(FileExistsError):
        prepare_python(verifier, python_donor)
    assert verifier.python_inventory(python_donor.donor) == before


def test_native_python_preserves_standard_terminfo_plus_names_and_contained_links(
    verifier, python_donor
):
    donor = python_donor.donor
    for name in ("share/terminfo/a/aaa+dec", "share/terminfo/x/xterm+256color"):
        path = donor / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x1a\x01 terminfo fixture\n")
    (donor / "share/terminfo/x/xterm+alias").symlink_to("xterm+256color")
    (donor / "share/terminfo/a/aaa+alias").symlink_to("../x/xterm+256color")
    before = verifier.python_inventory(donor)
    copied = prepare_python(verifier, python_donor).parent.parent
    assert (copied / "share/terminfo/a/aaa+dec").read_bytes() == b"\x1a\x01 terminfo fixture\n"
    assert (copied / "share/terminfo/x/xterm+alias").readlink() == Path("xterm+256color")
    assert (copied / "share/terminfo/a/aaa+alias").readlink() == Path("../x/xterm+256color")
    assert verifier.python_inventory(donor) == before
    for name, asset in (("src/xterm+256color.py", False), ("assets/xterm+256color.js", True)):
        with pytest.raises(ValueError, match="web release"):
            verifier.relative(name, asset=asset)


@pytest.mark.parametrize(
    "name", ["bad:name", "bad\\name", "bad name", "bad%name", "bad?name", "bad#name", "bad\nname"]
)
def test_native_python_names_still_refuse_delimiters_and_controls(verifier, python_donor, name):
    (python_donor.donor / "lib/python3.14" / name).write_bytes(b"invalid runtime name\n")
    with pytest.raises(ValueError, match="unsupported Python member name"):
        prepare_python(verifier, python_donor)
    assert not list(python_donor.root.glob("web-*"))


@pytest.mark.parametrize("target", ["xterm+256color:bad", "../../../../../outside", "/etc/passwd"])
def test_native_python_plus_link_names_do_not_permit_delimiters_or_escape(
    verifier, python_donor, target
):
    directory = python_donor.donor / "share/terminfo/x"
    directory.mkdir(parents=True)
    (directory / "xterm+alias").symlink_to(target)
    with pytest.raises(ValueError, match=r"Python link|unsupported Python"):
        prepare_python(verifier, python_donor)
    assert not list(python_donor.root.glob("web-*"))


@pytest.mark.parametrize(
    "damage",
    [
        "absolute-link",
        "escaping-link",
        "dangling-link",
        "cyclic-link",
        "installer-alias",
        "writable",
        "hardlink",
        "fifo",
        "unknown-pip",
        "pip-metadata",
        "patch-pin",
    ],
)
def test_native_python_refuses_unsafe_or_unrecognized_donor_before_destination(
    verifier, python_donor, damage
):
    donor = python_donor.donor
    if damage.endswith("-link") or damage == "installer-alias":
        target = {
            "absolute-link": "/outside",
            "escaping-link": "../../outside",
            "dangling-link": "missing",
            "cyclic-link": "unsafe",
            "installer-alias": "pip",
        }[damage]
        (donor / "bin/unsafe").symlink_to(target)
    elif damage == "writable":
        (donor / "lib/python3.14/os.py").chmod(0o666)
    elif damage == "hardlink":
        (donor / "lib/python3.14/alias.py").hardlink_to(donor / "lib/python3.14/os.py")
    elif damage == "fifo":
        os.mkfifo(donor / "bin/unsafe")
    elif damage == "unknown-pip":
        (donor / "bin/pip9").write_bytes(b"unknown installer; must not remove\n")
    elif damage == "pip-metadata":
        (donor / "lib/python3.14/site-packages/pip-26.1.2.dist-info/METADATA").write_bytes(
            b"Name: other-package\nVersion: 26.1.2\n"
        )
    else:
        (python_donor.source / ".python-version").write_text("3.14\n")
        python_donor.index["source_files"][".python-version"] = verifier.digest(b"3.14\n")
    with pytest.raises(ValueError, match=r"Python|python|web release"):
        prepare_python(verifier, python_donor)
    assert not list(python_donor.root.glob("web-*"))


def test_native_python_failed_copy_retains_private_partial_and_unchanged_donor(
    verifier, python_donor, monkeypatch
):
    before = verifier.python_inventory(python_donor.donor)
    original = verifier._write_new
    calls = []

    def fail(directory, name, body, **options):
        calls.append(name)
        original(directory, name, body, **options)
        message = "owned copy failure"
        raise OSError(message)

    monkeypatch.setattr(verifier, "_write_new", fail)
    with pytest.raises(OSError, match="owned copy failure"):
        prepare_python(verifier, python_donor)
    partial = next(python_donor.root.glob("web-*"))
    assert stat.S_IMODE(partial.stat().st_mode) == 0o700
    assert len(calls) == 1
    assert any(path.is_file() for path in partial.rglob("*"))
    assert verifier.python_inventory(python_donor.donor) == before
    with pytest.raises(FileExistsError):
        prepare_python(verifier, python_donor)
    assert len(calls) == 1


def test_native_python_refuses_donor_rewrite_even_when_original_bytes_are_restored(
    verifier, python_donor, monkeypatch
):
    original = verifier._write_new
    rewritten = False

    def change_donor(directory, name, body, **options):
        nonlocal rewritten
        original(directory, name, body, **options)
        if not rewritten:
            path = python_donor.donor / "lib/python3.14/os.py"
            raw = path.read_bytes()
            path.write_bytes(b"changed donor bytes\n")
            path.write_bytes(raw)
            rewritten = True

    monkeypatch.setattr(verifier, "_write_new", change_donor)
    with pytest.raises(ValueError, match="Python donor changed during copy"):
        prepare_python(verifier, python_donor)
    partial = next(python_donor.root.glob("web-*"))
    assert stat.S_IMODE(partial.stat().st_mode) == 0o700
    assert rewritten
    assert [row[2] for row in python_donor.probes] == [True]


def test_prepare_python_cli_emits_only_verified_executable_path(
    verifier, python_donor, monkeypatch, capsys
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "web-release.py",
            "prepare-python",
            "--release",
            str(python_donor.output),
            "--source",
            str(python_donor.source),
            "--index-sha256",
            python_donor.expected,
            "--interpreter",
            str(python_donor.interpreter),
            "--python-root",
            str(python_donor.root),
        ],
    )
    assert verifier.main() == 0
    result = capsys.readouterr()
    assert result.err == ""
    assert (
        result.out
        == str(
            python_donor.root
            / ("web-0.2.2-" + python_donor.index["source_commit"])
            / "bin/python3.14"
        )
        + "\n"
    )


def test_python_probe_runs_actual_isolated_test_runtime(verifier):
    base = Path(sys.base_prefix)
    version = ".".join(map(str, sys.version_info[:3]))
    minor = ".".join(version.split(".")[:2])
    managers = any(
        path.is_dir()
        for path in (
            base / f"lib/python{minor}/ensurepip",
            base / f"lib/python{minor}/site-packages/pip",
        )
    )
    verifier.probe_python(base / "bin" / ("python" + minor), version, base, managers=managers)


@pytest.mark.parametrize("bound", ["MAX_PYTHON_ENTRIES", "MAX_PYTHON_BYTES", "MAX_PYTHON_DEPTH"])
def test_native_python_capture_bounds_refuse_before_copy(
    verifier, python_donor, monkeypatch, bound
):
    monkeypatch.setattr(verifier, bound, 1)
    with pytest.raises(ValueError, match=r"Python.*(bound|exceeded)"):
        prepare_python(verifier, python_donor)
    assert not list(python_donor.root.glob("web-*"))
