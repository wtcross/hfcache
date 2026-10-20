"""WEB-003 owned read-fixture guards run before real local HTTP/browser effects."""

import json
import os
import runpy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = runpy.run_path(str(ROOT / "scripts/check-web-read-fixture.py"))


@pytest.fixture
def owner(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    (root / ".scratch").mkdir()
    return root


@pytest.mark.parametrize(
    "requested",
    [
        "/srv/hfcache/new",
        "/etc/hfcache/new",
        "../outside",
        ".scratch/../outside",
        ".scratch/./new",
        ".scratch",
        ".scratch/name with spaces",
    ],
)
def test_unsafe_read_fixture_workspace_refuses_before_target_access(owner, monkeypatch, requested):
    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append(args)
        pytest.fail("invalid workspace accessed a target or started a process")

    with monkeypatch.context() as guard:
        guard.setattr(Path, "lstat", forbidden)
        guard.setattr(Path, "mkdir", forbidden)
        with pytest.raises(ValueError, match="workspace"):
            FIXTURE["prepare_workspace"](requested, root=owner)
    assert attempts == []


def test_read_fixture_never_follows_a_symlinked_ancestor(owner, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (owner / ".scratch/alias").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="owned ordinary directories"):
        FIXTURE["prepare_workspace"](".scratch/alias/new", root=owner)
    assert list(outside.iterdir()) == []


def test_existing_unknown_workspace_is_preserved(owner):
    target = owner / ".scratch/unknown"
    target.mkdir()
    evidence = target / "evidence"
    evidence.write_bytes(b"unexplained original evidence")
    before = target.stat().st_ino, evidence.read_bytes()
    with pytest.raises(FileExistsError):
        FIXTURE["prepare_workspace"](".scratch/unknown", root=owner)
    assert (target.stat().st_ino, evidence.read_bytes()) == before
    assert not (target / "fixture.json").exists()


def test_new_fixture_is_owned_restricted_and_does_not_reuse_previous_evidence(owner):
    first = FIXTURE["prepare_workspace"](None, root=owner)
    second = FIXTURE["prepare_workspace"](None, root=owner)
    assert first != second
    assert first.is_relative_to(owner / ".scratch")
    assert first.stat().st_uid == os.getuid()
    assert first.stat().st_mode & 0o777 == 0o700
    marker = json.loads((first / "fixture.json").read_text())
    assert marker["purpose"] == "WEB-003-owned-read-fixture"
    assert (first / "fixture.json").stat().st_mode & 0o777 == 0o600


def test_fresh_checkout_can_create_only_its_fixed_scratch_parent(tmp_path):
    root = tmp_path / "fresh"
    root.mkdir()
    workspace = FIXTURE["prepare_workspace"](None, root=root)
    assert workspace.parent == root / ".scratch"
    assert workspace.parent.stat().st_mode & 0o777 == 0o700


def test_missing_arbitrary_nested_parent_is_refused_without_creating_scratch(tmp_path):
    root = tmp_path / "fresh"
    root.mkdir()
    with pytest.raises(ValueError, match="parents must already exist"):
        FIXTURE["prepare_workspace"](".scratch/unknown/new", root=root)
    assert not (root / ".scratch").exists()


@pytest.mark.parametrize("kind", ["nfs", "nfs4", "cifs", "autofs", "fuse.sshfs", "unknown"])
def test_mount_metadata_refuses_network_or_unknown_backing_without_target_traversal(
    kind, monkeypatch
):
    table = f"1 0 0:1 / / rw - xfs /dev/local rw\n2 1 0:2 / /owned/repo rw - {kind} remote rw\n"

    def forbidden(*args, **kwargs):
        pytest.fail("mount classification traversed the owned target")

    monkeypatch.setattr(Path, "stat", forbidden)
    monkeypatch.setattr(Path, "lstat", forbidden)
    with pytest.raises(ValueError, match="not proven"):
        FIXTURE["prove_local_path"](Path("/owned/repo/.scratch/new"), table)


def test_mount_metadata_uses_deepest_mount_and_decodes_escaped_mount_paths():
    table = (
        "1 0 0:1 / / rw - nfs4 remote rw\n2 1 0:2 / /owned/repo\\040copy rw - ext4 /dev/local rw\n"
    )
    FIXTURE["prove_local_path"](Path("/owned/repo copy/.scratch/new"), table)
    with pytest.raises(ValueError, match="not proven"):
        FIXTURE["prove_local_path"](Path("/owned/repo/.scratch/new"), table)


@pytest.mark.parametrize(
    "table", ["", "missing grammar", "1 0 0:1 / relative rw - xfs /dev/local rw\n"]
)
def test_unusable_mount_metadata_fails_closed(table):
    with pytest.raises(ValueError, match="filesystem"):
        FIXTURE["prove_local_path"](Path("/owned/repo/new"), table)


def test_help_precedes_workspace_and_runtime_discovery(monkeypatch, capsys):
    main = FIXTURE["main"]

    def forbidden(*args, **kwargs):
        pytest.fail("safe help touched fixture/runtime state")

    monkeypatch.setitem(main.__globals__, "prepare_workspace", forbidden)
    monkeypatch.setitem(main.__globals__, "run", forbidden)
    monkeypatch.setattr(sys, "argv", ["check-web-read-fixture.py", "--help"])
    with pytest.raises(SystemExit) as stopped:
        main()
    assert stopped.value.code == 0
    assert "--workspace" in capsys.readouterr().out


def test_fixture_child_environment_drops_ambient_application_credentials(owner, monkeypatch):
    workspace = FIXTURE["prepare_workspace"](None, root=owner)
    for name in (
        "HF_TOKEN",
        "HF_HOME",
        "HFCACHE_CONFIG",
        "HFCACHE_API_TOKEN",
        "HTTPS_PROXY",
        "SSL_CERT_FILE",
        "NODE_OPTIONS",
    ):
        monkeypatch.setenv(name, "never inherit this fixture marker")
    env = FIXTURE["environment"](workspace)
    assert all("never inherit" not in value for value in env.values())
    assert set(env) <= {
        "PATH",
        "HOME",
        "PNPM_HOME",
        "LANG",
        "LC_ALL",
        "TMPDIR",
        "PLAYWRIGHT_BROWSERS_PATH",
    }


def test_roundtrip_corpus_uses_original_models_and_independent_incorrect_values():
    corpus = FIXTURE["model_corpus"]()
    assert len(corpus["originals"]) >= 200
    assert len(corpus["incorrect"]) == 4
    assert {case["definition"] for case in corpus["originals"]} >= {
        "Reference",
        "RevisionManifest",
        "RunReport",
        "VerificationReport",
        "PrunePlan",
        "PurgePlan",
    }
    assert {case["case_id"] for case in corpus["incorrect"]} == {
        "incorrect-read-version-null-identities",
        "incorrect-reader-false-capabilities",
        "incorrect-complete-zero-byte-variant",
        "incorrect-exact-publication-reference",
    }
