"""Read-only administrator proposal; temporary trees do not prove deployment.

Profile fixtures inject the policy implementation to test proposed authorities;
the separate bootstrap tests exercise actual protected capture and code loading.
"""

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache import host_policy as policy
from tests.unit.test_host_policy import (
    deployment as deployment,  # noqa: PLC0414 - original indexed-stage dependency
)
from tests.unit.test_host_policy import (
    native as native,  # noqa: PLC0414 - real temporary ordinary native tree
)
from tests.unit.test_host_policy import native_uv_aliases
from tests.unit.test_host_policy import (
    rootless as rootless,  # noqa: PLC0414 - original staged tree and bindings
)

SCRIPT = Path(__file__).parents[2] / "scripts/prepare-host-helper.py"
SPEC = importlib.util.spec_from_file_location("prepare_host_helper", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def configure(host, monkeypatch):
    monkeypatch.setattr(tool, "OWNER", os.geteuid())
    account = SimpleNamespace(
        pw_uid=host.index["api_principal"]["host_uid"],
        pw_gid=host.index["api_principal"]["host_gid"],
        pw_dir="/var/lib/hfcache",
    )

    def fixed_account(name):
        assert name == "hfcache"
        return account

    monkeypatch.setattr(tool.pwd, "getpwnam", fixed_account)
    # The injected fixture's selected/bootstrap module bytes are deliberate
    # inert unit inputs; actual load_policy capture is tested separately.
    monkeypatch.setattr(
        policy, "_bootstrap_sha256", host.index["bindings"]["helper_policy_module"], raising=False
    )
    monkeypatch.setattr(tool, "load_policy", lambda: policy)
    return account


@pytest.mark.parametrize("fixture", ["native", "rootless"])
def test_proposal_matches_actual_leaf_bytes_modes_and_fixed_bindings(fixture, request, monkeypatch):
    host = request.getfixturevalue(fixture)
    configure(host, monkeypatch)
    before = {name: (host.selected / name).read_bytes() for name in host.index["authority_files"]}
    proposed = tool.prepare(policy, fixture, "c" * 40, "d" * 64, dirty=True)
    assert policy._deployment(json.dumps(proposed).encode()) == proposed
    assert proposed["source"] == {
        "parent_commit": "c" * 40,
        "snapshot_sha256": "d" * 64,
        "dirty": True,
    }
    assert proposed["bindings"] == host.index["bindings"]
    assert proposed["authority_files"] == host.index["authority_files"]
    assert proposed["profile_evidence"] == host.index["profile_evidence"]
    assert before == {name: (host.selected / name).read_bytes() for name in before}


def test_native_inventory_keeps_existing_cache_bytes_and_large_real_runtime(native, monkeypatch):
    configure(native, monkeypatch)
    target = policy.PREFIX / "python" / native.index["profile_evidence"]["python_target_relative"]
    body = b"x" * (policy.MAX_AUTHORITY_BYTES + 1)
    target.write_bytes(body)
    proposed = tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)
    assert proposed["profile_evidence"]["python_target_sha256"] == hashlib.sha256(body).hexdigest()
    assert any(name.endswith(".pyc") for name in proposed["authority_files"])


def test_native_proposal_uses_original_uv_minor_alias_and_canonical_hash(native, monkeypatch):
    configure(native, monkeypatch)
    _selector, target = native_uv_aliases(native)
    proposed = tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)
    assert (
        proposed["profile_evidence"]["python_target_relative"]
        == target.relative_to(policy.PREFIX / "python").as_posix()
    )
    assert (
        proposed["profile_evidence"]["python_target_sha256"]
        == hashlib.sha256(target.read_bytes()).hexdigest()
    )
    assert not any(
        name.endswith(("/python", "/python3", "/python3.14"))
        for name in proposed["authority_files"]
    )


def test_preparation_never_reads_policy_key_configuration_or_archive(native, monkeypatch):
    configure(native, monkeypatch)
    for path in (native.policy, native.deployment, native.key, native.config):
        path.unlink()
    original = os.open

    def observed(path, flags, *args, **kwargs):
        assert not flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR | os.O_TRUNC)
        assert not str(path).startswith("/srv")
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", observed)
    assert tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)["profile"] == "native"
    assert native.calls == []
    assert not any(
        path.exists() for path in (native.policy, native.deployment, native.key, native.config)
    )


@pytest.mark.parametrize(
    "change",
    ["commit", "snapshot", "dirty", "profile", "bootstrap", "account", "binding", "selector"],
)
def test_uncertain_or_unbound_proposal_inputs_refuse(native, monkeypatch, change):
    account = configure(native, monkeypatch)
    commit, snapshot, dirty, profile = "c" * 40, "d" * 64, True, "native"
    if change == "commit":
        commit = "synthetic-commit"
    elif change == "snapshot":
        snapshot = "A" * 64
    elif change == "dirty":
        dirty = 1
    elif change == "profile":
        profile = "other"
    elif change == "bootstrap":
        monkeypatch.setattr(policy, "_bootstrap_sha256", "0" * 64)
    elif change == "account":
        account.pw_dir = "/unreviewed"
    elif change == "binding":
        fixed = policy.binding_paths("native")["helper_daemon"][0]
        fixed.write_bytes(fixed.read_bytes() + b"changed")
    else:
        selector = policy.PREFIX / "current"
        selector.unlink()
        selector.symlink_to("releases/../0.2.0")
    with pytest.raises((ValueError, OSError)):
        tool.prepare(policy, profile, commit, snapshot, dirty)


def test_rootless_parent_commit_and_original_stage_are_rechecked(rootless, monkeypatch):
    configure(rootless, monkeypatch)
    with pytest.raises(ValueError, match="protected host index preparation refused"):
        tool.prepare(policy, "rootless", "e" * 40, "d" * 64, dirty=True)
    path = rootless.selected / "rendered/server.toml"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match=r"."):
        tool.prepare(policy, "rootless", "c" * 40, "d" * 64, dirty=True)


def test_main_emits_only_proposed_index_and_requires_explicit_provenance_state(
    native, monkeypatch, capsys
):
    configure(native, monkeypatch)
    args = ["--profile", "native", "--source-commit", "c" * 40, "--source-snapshot", "d" * 64]
    with pytest.raises(SystemExit) as result:
        tool.main(args)
    assert result.value.code == 2
    capsys.readouterr()
    assert tool.main([*args, "--source-dirty"]) == 0
    output = capsys.readouterr()
    value = json.loads(output.out)
    assert value["source"]["dirty"] is True
    assert output.err == ""
    assert "permissions" not in value
    assert "revision" not in value


@pytest.mark.parametrize("kind", ["regular", "symlink", "writable", "hardlink", "oversize", "fifo"])
def test_actual_fixed_bootstrap_capture_is_protected_bounded_and_has_no_package_imports(
    tmp_path, monkeypatch, kind
):
    path = tmp_path / "lib/host_policy.py"
    path.parent.mkdir()
    path.write_bytes((SCRIPT.parents[1] / "src/hfcache/host_policy.py").read_bytes())
    path.chmod(0o644)
    monkeypatch.setattr(tool, "OWNER", os.geteuid())
    monkeypatch.setattr(tool, "LIBRARY", path)
    if kind == "symlink":
        other = path.with_name("other.py")
        path.rename(other)
        path.symlink_to(other)
    elif kind == "writable":
        path.chmod(0o666)
    elif kind == "hardlink":
        os.link(path, path.with_name("second.py"))
    elif kind == "oversize":
        path.write_bytes(b"x" * (tool.MAX_BOOTSTRAP + 1))
    elif kind == "fifo":
        path.unlink()
        os.mkfifo(path)
    if kind == "regular":
        module = tool.load_policy()
        assert module._bootstrap_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
        assert module.InspectionBudget().remaining() <= 5
    else:
        with pytest.raises((ValueError, OSError)):
            tool.load_policy()


def test_help_has_no_host_reads_and_source_has_no_mutation_primitives(monkeypatch, capsys):
    def forbidden():
        pytest.fail("help attempted protected host reads")

    monkeypatch.setattr(tool, "load_policy", forbidden)
    with pytest.raises(SystemExit) as result:
        tool.main(["--help"])
    assert result.value.code == 0
    assert "Propose a fixed host-helper deployment index" in capsys.readouterr().out
    tree = ast.parse(SCRIPT.read_bytes(), feature_version=(3, 12))
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write_bytes", "write_text", "mkdir", "unlink", "execv", "flock"}
        for node in ast.walk(tree)
    )
