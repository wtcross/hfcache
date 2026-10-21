"""Actual protected local capture and adversarial immutable-artifact boundaries."""

import hashlib
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from hfcache.api import ui_assets
from hfcache.api.ui_assets import CapturedMember, capture_assets, parse_mount_snapshot, render_shell
from hfcache.errors import ConfigurationError
from hfcache.models import dump
from hfcache.reporting import RuntimeVersions
from hfcache.server_config import CredentialSource, TLSConfig, WebConfig
from hfcache.ui_models import UiAssetManifest
from tests.fixtures.web_ui import SHELL, WIRE_DIGEST, make_profile


def capture(profile):
    return capture_assets(
        profile.server,
        profile.policy,
        state_root=profile.server.state_directory,
        instance_lock_path=profile.lock,
        application_version=RuntimeVersions.measured().application,
        wire_source_digest=WIRE_DIGEST,
        environ={},
    )


def test_real_capture_pins_bytes_and_closes_the_only_retained_root_descriptor():
    profile = make_profile(prefix="/管理'quoted")
    result = capture(profile)
    assert result is not None
    fd = result.root_descriptor
    assert os.fstat(fd).st_ino == profile.assets.stat().st_ino
    assert (
        result.members["assets/main-AbCd1234.js"].body == profile.bodies["assets/main-AbCd1234.js"]
    )
    assert result.members["assets/main-AbCd1234.js"].private_cache
    assert b"/\xe7\xae\xa1" not in result.shells["/管理'quoted"]
    assert b"/ui/" in result.shells[""]
    assert b"%E7%AE%A1%E7%90%86&#x27;quoted/ui/" in result.shells["/管理'quoted"]
    (profile.assets / "assets/main-AbCd1234.js").write_bytes(b"changed after startup")
    assert (
        result.members["assets/main-AbCd1234.js"].body == profile.bodies["assets/main-AbCd1234.js"]
    )
    result.close()
    result.close()
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(fd)
    assert not result.members


def test_disabled_web_performs_no_asset_or_mount_access(monkeypatch):
    profile = make_profile()
    profile.server = profile.server.model_copy(
        update={"web": WebConfig.model_validate({"asset_root": "/srv/hfcache/NEVER-OPEN"})}
    )
    monkeypatch.setattr(
        ui_assets, "read_mount_snapshot", lambda: pytest.fail("disabled mount access")
    )
    monkeypatch.setattr(
        ui_assets.os, "open", lambda *_a, **_kw: pytest.fail("disabled asset access")
    )
    assert capture(profile) is None


@pytest.mark.parametrize(
    "kind",
    ["unknown", "symlink", "hardlink", "fifo", "writable", "mutation", "manifest", "duplicate"],
)
def test_capture_refuses_actual_unknown_alias_special_or_changed_bytes(kind):
    profile = make_profile()
    target = profile.assets / "assets/main-AbCd1234.js"
    if kind == "unknown":
        (profile.assets / "unknown.js").write_bytes(b"unindexed")
    elif kind == "symlink":
        original = target.with_suffix(".original")
        target.rename(original)
        target.symlink_to(original)
    elif kind == "hardlink":
        os.link(target, profile.root / "outside-hardlink")
    elif kind == "fifo":
        target.unlink()
        os.mkfifo(target)
    elif kind == "writable":
        target.chmod(0o666)
    elif kind == "mutation":
        target.write_bytes(b"x" * len(profile.bodies["assets/main-AbCd1234.js"]))
    elif kind == "manifest":
        (profile.assets / "manifest.json").write_bytes(
            (profile.assets / "manifest.json").read_bytes() + b"\n"
        )
        profile.repin()
    else:
        manifest = profile.assets / "manifest.json"
        raw = manifest.read_bytes().replace(
            b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'
        )
        manifest.write_bytes(raw)
        profile.repin()
    with pytest.raises(ConfigurationError, match="enabled UI artifact"):
        capture(profile)


def test_file_identity_change_is_refused_even_when_approved_bytes_are_restored(monkeypatch):
    profile = make_profile()
    target = profile.assets / "assets/main-AbCd1234.js"
    inode = target.stat().st_ino
    original = os.read
    changed = False

    def read(fd, maximum):
        nonlocal changed
        result = original(fd, maximum)
        if os.fstat(fd).st_ino == inode and not changed:
            changed = True
            target.write_bytes(profile.bodies["assets/main-AbCd1234.js"])
        return result

    monkeypatch.setattr(ui_assets.os, "read", read)
    with pytest.raises(ConfigurationError):
        capture(profile)
    assert changed


def test_mount_bind_alias_is_rejected_without_opening_the_protected_target(monkeypatch):
    profile = make_profile()
    real = ui_assets.read_mount_snapshot()
    selected = real.select(profile.assets)
    device = f"{selected.device[0]}:{selected.device[1]}"
    raw = (
        f"1 0 {device} / / rw - ext4 owned rw\n"
        f"2 1 {device} {profile.policy.root} {profile.assets} rw - ext4 owned rw\n"
    ).encode()
    monkeypatch.setattr(ui_assets, "read_mount_snapshot", lambda: parse_mount_snapshot(raw))
    monkeypatch.setattr(ui_assets.os, "open", lambda *_a, **_kw: pytest.fail("alias target opened"))
    with pytest.raises(ConfigurationError):
        capture(profile)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"bad\n",
        b"1 0 1:2 relative / rw - ext4 own rw\n",
        b"1 0 1:2 / / rw - ext4 own rw\n1 0 1:2 / /other rw - ext4 own rw\n",
        b"1 0 1:2 / / rw - ext4 own rw\n2 0 1:2 / / rw - ext4 own rw\n",
        b"1 0 1:2 /bad\\777 / rw - ext4 own rw\n",
    ],
)
def test_malformed_or_ambiguous_mount_identity_refuses(raw):
    with pytest.raises(ConfigurationError):
        parse_mount_snapshot(raw).select(Path("/"))


@pytest.mark.parametrize(
    "changed",
    [
        SHELL.replace(b"<base href=", b'<base target="_blank" href='),
        SHELL.replace(b'<base href="__HFCACHE_UI_BASE_V1__">', b"<!--__HFCACHE_UI_BASE_V1__-->"),
        SHELL.replace(b'<div id="root">', b'<div id="root" onclick="alert(1)">'),
        SHELL.replace(b"<title>", b"<style>body{}</style><title>"),
        SHELL.replace(
            b"</head>", b'<meta http-equiv="refresh" content="0;url=https://else.invalid"></head>'
        ),
        SHELL.replace(b'src="./assets/main-AbCd1234.js"', b'src="https://else.invalid/main.js"'),
        SHELL.replace(b"</script>", b"alert(1)</script>"),
        SHELL.replace(b"Reload interface", b"Remove recovery"),
        SHELL.replace(b"<body>", b"<body><svg><script>alert(1)</script></svg>"),
    ],
)
def test_actual_html_parser_refuses_misplaced_tokens_execution_and_external_urls(changed):
    members = {
        "assets/main-AbCd1234.js": CapturedMember(b"", "text/javascript", private_cache=True),
        "assets/main-AbCd1234.css": CapturedMember(b"", "text/css", private_cache=True),
    }
    with pytest.raises(ConfigurationError):
        render_shell(changed, members, prefix="", fingerprint="d" * 64)


def test_toolchain_digest_is_checked_by_capture_context():
    profile = make_profile()
    path = profile.assets / "manifest.json"
    value = json.loads(path.read_bytes())
    value["build"]["toolchain_sha256"] = "e" * 64
    path.write_bytes((json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
    profile.repin()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == profile.server.web.manifest_sha256
    with pytest.raises(ConfigurationError):
        capture(profile)


def test_unambiguous_parent_linked_overmount_maps_the_visible_filesystem():
    mounts = parse_mount_snapshot(
        b"1 0 8:1 / / rw - ext4 root rw\n2 1 0:1 / /archive rw - autofs none rw\n"
        b"3 2 0:2 /export /archive rw - nfs4 owned rw\n"
    )
    assert mounts.select(Path("/archive/not-opened")).mount_id == 3
    assert mounts.physical(Path("/archive/not-opened")) == ((0, 2), Path("/export/not-opened"))


@pytest.mark.parametrize(
    "rows",
    [
        b"1 2 8:1 / / rw - ext4 root rw\n2 1 8:1 / / rw - ext4 root rw\n",
        (
            b"1 0 8:1 / / rw - ext4 root rw\n2 1 8:1 / / rw - ext4 root rw\n"
            b"3 1 8:1 / / rw - ext4 root rw\n"
        ),
    ],
)
def test_selected_mount_stack_cycles_or_branches_are_not_guessed(rows):
    with pytest.raises(ConfigurationError):
        parse_mount_snapshot(rows).select(Path("/"))


@pytest.mark.parametrize("kind", ["ancestor-mode", "root-mode", "root-symlink", "directory-mode"])
def test_every_protected_asset_ancestor_and_directory_is_checked(kind):
    profile = make_profile()
    if kind == "ancestor-mode":
        profile.root.chmod(0o770)
    elif kind == "root-mode":
        profile.assets.chmod(0o777)
    elif kind == "directory-mode":
        (profile.assets / "assets").chmod(0o777)
    else:
        moved = profile.root / "moved-artifact"
        profile.assets.rename(moved)
        profile.assets.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ConfigurationError):
        capture(profile)


@pytest.mark.parametrize(
    "budget",
    [
        "MAX_MANIFEST_BYTES",
        "MAX_MEMBER_BYTES",
        "MAX_FILES",
        "MAX_DIRECTORIES",
        "MAX_ENTRIES",
        "MAX_TOTAL_BYTES",
        "MAX_DEPTH",
    ],
)
def test_capture_stops_on_actual_independent_collection_budgets(monkeypatch, budget):
    profile = make_profile()
    monkeypatch.setattr(ui_assets, budget, 0)
    with pytest.raises(ConfigurationError):
        capture(profile)


def test_exact_manifest_and_aggregate_byte_limits_accept_without_overread(monkeypatch):
    profile = make_profile()
    monkeypatch.setattr(
        ui_assets, "MAX_MANIFEST_BYTES", (profile.assets / "manifest.json").stat().st_size
    )
    monkeypatch.setattr(ui_assets, "MAX_TOTAL_BYTES", sum(map(len, profile.bodies.values())))
    result = capture(profile)
    assert result is not None
    result.close()


def test_empty_unindexed_directories_cannot_exceed_the_tree_depth():
    profile = make_profile()
    path = profile.assets / "assets"
    for number in range(ui_assets.MAX_DEPTH):
        path /= f"empty{number}"
        path.mkdir()
    with pytest.raises(ConfigurationError):
        capture(profile)


def test_directory_insertion_after_enumeration_is_refused(monkeypatch):
    profile = make_profile()
    inode = profile.assets.stat().st_ino
    original = os.scandir

    @contextmanager
    def scan(fd):
        with original(fd) as entries:
            yield entries
        if os.fstat(fd).st_ino == inode:
            (profile.assets / "late-unindexed.js").write_bytes(b"late")

    monkeypatch.setattr(ui_assets.os, "scandir", scan)
    with pytest.raises(ConfigurationError):
        capture(profile)


def test_mount_snapshot_change_or_network_asset_root_refuses_without_archive_io(monkeypatch):
    profile = make_profile()
    snapshot = ui_assets.read_mount_snapshot()
    results = iter((snapshot, replace(snapshot, raw=snapshot.raw + b"changed")))
    monkeypatch.setattr(ui_assets, "read_mount_snapshot", lambda: next(results))
    with pytest.raises(ConfigurationError):
        capture(profile)
    network = parse_mount_snapshot(b"1 0 0:1 / / rw - nfs4 not-contacted rw\n")
    monkeypatch.setattr(ui_assets, "read_mount_snapshot", lambda: network)
    monkeypatch.setattr(
        ui_assets.os, "open", lambda *_a, **_kw: pytest.fail("network asset root opened")
    )
    with pytest.raises(ConfigurationError):
        capture(profile)


def test_effective_store_overlap_refuses_before_any_asset_open(monkeypatch):
    profile = make_profile()
    monkeypatch.setattr(
        ui_assets.os, "open", lambda *_a, **_kw: pytest.fail("overlapping root opened")
    )
    with pytest.raises(ConfigurationError):
        capture_assets(
            profile.server,
            profile.policy,
            state_root=profile.assets,
            instance_lock_path=profile.lock,
            application_version="0.2.2",
            wire_source_digest=WIRE_DIGEST,
            environ={},
        )


def test_known_tls_and_resolved_delivery_authorities_are_excluded_without_target_io(monkeypatch):
    profile = make_profile()
    delivery = profile.root / "never-open-delivery"
    tls = profile.root / "never-open-tls"
    source = CredentialSource(systemd_name="hfcache.ui-administrator")
    assert profile.server.basic is not None
    configured = profile.server.model_copy(
        update={
            "basic": profile.server.basic.model_copy(update={"administrator": source}),
            "listener": profile.server.listener.model_copy(
                update={
                    "tls": TLSConfig.model_validate(
                        {"certificate": str(tls / "public.crt"), "private_key": str(tls / "key")}
                    )
                }
            ),
        }
    )
    monkeypatch.setattr(ui_assets.os, "open", lambda *_a, **_kw: pytest.fail("authority opened"))
    excluded = ui_assets.forbidden_paths(
        configured,
        profile.policy,
        state_root=profile.server.state_directory,
        instance_lock_path=profile.lock,
        hub_token_file=profile.root / "hub" / "token",
        environ={"CREDENTIALS_DIRECTORY": str(delivery)},
    )
    assert {
        delivery,
        delivery / "hfcache.ui-administrator",
        tls,
        tls / "key",
        tls / "public.crt",
        profile.root / "hub",
        profile.root / "hub" / "token",
        profile.policy.root,
        profile.policy.path,
        profile.server.state_directory,
        profile.server.listener.unix_address,
        profile.server.verification.unix_socket,
        profile.lock,
    } <= set(excluded)


@pytest.mark.parametrize("replace_ancestor", [True, False])
def test_final_ancestry_rewalk_rejects_replacement_but_allows_unrelated_siblings(
    monkeypatch, replace_ancestor
):
    profile = make_profile()
    outer = profile.root / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    assets = inner / "artifact"
    profile.assets.rename(assets)
    profile.server = profile.server.model_copy(
        update={
            "web": WebConfig.model_validate(
                {
                    "enabled": True,
                    "asset_root": str(assets),
                    "manifest_sha256": profile.server.web.manifest_sha256,
                }
            )
        }
    )
    inode = assets.stat().st_ino
    original = os.scandir
    changed = False

    @contextmanager
    def scan(fd):
        nonlocal changed
        with original(fd) as entries:
            yield entries
        if os.fstat(fd).st_ino == inode and not changed:
            changed = True
            if replace_ancestor:
                outer.rename(profile.root / "old-outer-retained")
                (outer / "inner").mkdir(parents=True)
            else:
                (profile.root / "unrelated-sibling").write_bytes(b"unrelated")

    monkeypatch.setattr(ui_assets.os, "scandir", scan)
    if replace_ancestor:
        with pytest.raises(ConfigurationError):
            capture(profile)
    else:
        result = capture(profile)
        assert result is not None
        result.close()
    assert changed


def test_maximum_manifest_does_not_retain_one_descriptor_per_member():
    profile = make_profile()
    manifest_path = profile.assets / "manifest.json"
    value = json.loads(manifest_path.read_bytes())
    for number in range(4096 - len(value["members"])):
        name = f"assets/extra{number}.js"
        (profile.assets / name).write_bytes(b"")
        value["members"].append(
            {
                "path": name,
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
                "mime": "text/javascript",
            }
        )
    value["members"].sort(key=lambda row: row["path"])
    manifest_path.write_bytes(dump(UiAssetManifest.model_validate(value)))
    profile.repin()
    server_path = profile.root / "server.json"
    server_path.write_text(profile.server.model_dump_json())
    code = """import json,resource,sys
from pathlib import Path
from hfcache.api.ui_assets import capture_assets
from hfcache.server_config import InstalledPolicy,ServerConfig
server=ServerConfig.model_validate(json.loads(Path(sys.argv[1]).read_bytes()))
policy=InstalledPolicy.open(server)
resource.setrlimit(resource.RLIMIT_NOFILE,(32,resource.getrlimit(resource.RLIMIT_NOFILE)[1]))
capture=capture_assets(server,policy,state_root=server.state_directory,instance_lock_path=Path(sys.argv[2]),application_version=sys.argv[3],wire_source_digest='a'*64,environ={})
assert capture is not None and len(capture.members)==4096
capture.close()
print(json.dumps({'members':4096,'descriptor_limit':32,'closed':True}))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(server_path),
            str(profile.lock),
            RuntimeVersions.measured().application,
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"members": 4096, "descriptor_limit": 32, "closed": True}
