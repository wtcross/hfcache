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
    native_web as native_web,  # noqa: PLC0414 - full indexed closure
)
from tests.unit.test_host_policy import (
    rootless as rootless,  # noqa: PLC0414 - original staged tree and bindings
)
from tests.unit.test_host_policy import (
    rootless_web as rootless_web,  # noqa: PLC0414 - indexed web stage and bounded reads
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


def test_rootless_web_proposal_keeps_complete_empty_and_nonempty_asset_authority(
    rootless_web, monkeypatch
):
    configure(rootless_web, monkeypatch)
    proposed = tool.prepare(policy, "rootless", "c" * 40, "d" * 64, dirty=True)
    assert proposed["authority_files"] == rootless_web.index["authority_files"]
    assert proposed["bindings"] == rootless_web.index["bindings"]
    assert proposed["profile_evidence"] == rootless_web.index["profile_evidence"]
    assert "ui/assets/app-12345678.js" in proposed["authority_files"]


def test_native_web_proposal_keeps_index_complete_ui_and_nine_helper_artifacts(
    native_web, monkeypatch
):
    configure(native_web, monkeypatch)
    proposed = tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)
    assert proposed["authority_files"] == native_web.index["authority_files"]
    assert proposed["bindings"] == native_web.index["bindings"]
    assert "web-release.json" in proposed["authority_files"]
    assert proposed["authority_files"]["ui/assets/app-12345678.js"]["bytes"] == 0
    assert (
        len([name for name in proposed["authority_files"] if name.startswith("host-helper/")]) == 9
    )


def observer_fragment(native, monkeypatch):
    fixed = (
        native.selected.parent.parent / "systemd/hfcache-sync.service.d/50-hfcache-observer.conf"
    )
    template = native.selected / policy.SYNC_OBSERVER_RELATIVE
    body = b"[Service]\nSELinuxContext=system_u:system_r:hfcache_sync_observer_t:s0\n"
    monkeypatch.setattr(policy, "SYNC_OBSERVER_DROP_IN", fixed)
    fixed.parent.parent.mkdir(parents=True, exist_ok=True)
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_bytes(body)
    template.chmod(0o644)
    return fixed, template, body


def test_native_observer_provisioning_is_explicit_and_never_created(native, monkeypatch):
    configure(native, monkeypatch)
    fixed, _template, _body = observer_fragment(native, monkeypatch)
    proposed = tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)
    assert policy.SYNC_OBSERVER_BINDING not in proposed["bindings"]
    assert not fixed.parent.exists()


def test_native_observer_proposal_binds_exact_protected_fragment_and_selected_template(
    native, monkeypatch
):
    configure(native, monkeypatch)
    fixed, template, body = observer_fragment(native, monkeypatch)
    fixed.parent.mkdir(parents=True)
    fixed.write_bytes(body)
    fixed.chmod(0o644)
    before = tuple(getattr(fixed.stat(), name) for name in policy.METADATA)
    proposed = tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)
    assert proposed["bindings"][policy.SYNC_OBSERVER_BINDING] == hashlib.sha256(body).hexdigest()
    assert (
        proposed["authority_files"][policy.SYNC_OBSERVER_RELATIVE]["sha256"]
        == hashlib.sha256(template.read_bytes()).hexdigest()
    )
    assert before == tuple(getattr(fixed.stat(), name) for name in policy.METADATA)
    assert policy._deployment(json.dumps(proposed).encode()) == proposed


@pytest.mark.parametrize("change", ["link", "hardlink", "mode", "extra", "minus", "command"])
def test_observer_proposal_refuses_unsafe_or_broader_fragment(native, monkeypatch, change):
    configure(native, monkeypatch)
    fixed, template, body = observer_fragment(native, monkeypatch)
    fixed.parent.mkdir(parents=True)
    if change == "link":
        fixed.symlink_to(template)
    elif change == "hardlink":
        os.link(template, fixed)
    else:
        if change == "minus":
            body = body.replace(b"SELinuxContext=", b"SELinuxContext=-")
        elif change == "command":
            body += b"ExecStart=/bin/sh\n"
        fixed.write_bytes(body)
        fixed.chmod(0o666 if change == "mode" else 0o644)
        if change == "extra":
            (fixed.parent / "99-unknown.conf").write_bytes(b"[Service]\n")
    with pytest.raises((OSError, ValueError, policy.InspectionError)):
        tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)


def test_observer_fragment_appearance_or_change_cannot_race_the_readonly_proposal(
    native, monkeypatch
):
    configure(native, monkeypatch)
    fixed, _template, body = observer_fragment(native, monkeypatch)
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = [(Path("/"), "ext4", {"rw"}, {"rw"})]
    assert tool.optional_observer_context(policy, capture, "native") is False
    fixed.parent.mkdir(parents=True)
    fixed.write_bytes(body)
    fixed.chmod(0o644)
    with pytest.raises(policy.InspectionError):
        capture.revalidate()
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = [(Path("/"), "ext4", {"rw"}, {"rw"})]
    assert tool.optional_observer_context(policy, capture, "native") is True
    fixed.write_bytes(body + b"# changed\n")
    with pytest.raises(policy.InspectionError):
        capture.revalidate()


def test_rootless_proposal_never_adopts_even_a_present_native_observer_fragment(
    native, monkeypatch
):
    configure(native, monkeypatch)
    fixed, template, _body = observer_fragment(native, monkeypatch)
    fixed.parent.mkdir(parents=True)
    fixed.symlink_to(template)
    capture = policy._Capture(policy.InspectionBudget())
    assert tool.optional_observer_context(policy, capture, "rootless") is False
    assert not capture.files
    assert not capture.links
    assert not capture.parents


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
    labels = path.with_name("host_selinux.py")
    labels.write_bytes((SCRIPT.parents[1] / "src/hfcache/host_selinux.py").read_bytes())
    labels.chmod(0o644)
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
        assert (
            module._host_labels._bootstrap_sha256 == hashlib.sha256(labels.read_bytes()).hexdigest()
        )
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


@pytest.mark.parametrize("kind", ["missing", "writable", "symlink", "hardlink"])
def test_label_bootstrap_must_be_protected_before_the_policy_module_executes(
    tmp_path, monkeypatch, kind
):
    path = tmp_path / "host_policy.py"
    path.write_bytes(b"raise AssertionError('unvalidated policy executed')\n")
    path.chmod(0o644)
    labels = path.with_name("host_selinux.py")
    labels.write_bytes((SCRIPT.parents[1] / "src/hfcache/host_selinux.py").read_bytes())
    labels.chmod(0o644)
    monkeypatch.setattr(tool, "OWNER", os.geteuid())
    monkeypatch.setattr(tool, "LIBRARY", path)
    if kind == "missing":
        labels.unlink()
    elif kind == "writable":
        labels.chmod(0o666)
    elif kind == "symlink":
        original = labels.with_name("original.py")
        labels.rename(original)
        labels.symlink_to(original)
    else:
        os.link(labels, labels.with_name("alias.py"))
    with pytest.raises((ValueError, OSError)):
        tool.load_policy()


def test_readonly_rootless_proposal_binds_preserved_alternate_home(rootless, monkeypatch):
    account = configure(rootless, monkeypatch)
    account.pw_dir = "/var/lib/hfcache/container-home"
    before = {
        name: (rootless.selected / name).read_bytes() for name in rootless.index["authority_files"]
    }
    proposed = tool.prepare(policy, "rootless", "c" * 40, "d" * 64, dirty=True)
    assert proposed["profile_evidence"]["account_home"] == account.pw_dir
    assert (
        proposed["profile_evidence"]["runtime_profile_sha256"]
        == rootless.index["profile_evidence"]["runtime_profile_sha256"]
    )
    assert before == {name: (rootless.selected / name).read_bytes() for name in before}


def test_native_proposal_refuses_rootless_alternate_account_home(native, monkeypatch):
    account = configure(native, monkeypatch)
    account.pw_dir = "/var/lib/hfcache/container-home"
    with pytest.raises(ValueError, match="protected host index preparation refused"):
        tool.prepare(policy, "native", "c" * 40, "d" * 64, dirty=True)
