"""Closed account-home compatibility; no live account, engine or archive access."""

import json
import os
import socket
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from hfcache import host_peer as peer
from hfcache import host_policy as policy
from hfcache.host_protocol import LivePeer
from tests.unit.test_host_engine import budget as engine_budget
from tests.unit.test_host_engine import storage as storage  # noqa: PLC0414 - owned storage fixture
from tests.unit.test_host_engine_locks import budget as lock_budget
from tests.unit.test_host_engine_locks import locks as locks  # noqa: PLC0414 - owned lock fixture
from tests.unit.test_host_policy import (
    deployment as deployment,  # noqa: PLC0414 - transitive fixture
)
from tests.unit.test_host_policy import native as native  # noqa: PLC0414 - owned native fixture
from tests.unit.test_host_policy import (
    rootless as rootless,  # noqa: PLC0414 - owned rootless fixture
)

DEFAULT = "/var/lib/hfcache"
CONTAINER = "/var/lib/hfcache/container-home"
UID = GID = 983


def indexed_account(home=None, *, profile="rootless"):
    evidence = {} if home is None else {"account_home": home}
    return {
        "profile": profile,
        "api_principal": {"host_uid": UID, "host_gid": GID},
        "profile_evidence": evidence,
    }


@pytest.mark.parametrize("home", [DEFAULT, CONTAINER])
def test_bound_home_selects_one_exact_existing_account_without_ambient_fallback(home, monkeypatch):
    account = SimpleNamespace(pw_uid=UID, pw_gid=GID, pw_dir=home)
    monkeypatch.setattr(peer.pwd, "getpwnam", lambda name: account if name == "hfcache" else None)
    monkeypatch.setenv("HOME", "/unselected")
    assert peer._account_home(indexed_account(home)) == home
    environment = peer._environment(UID, home=home)
    assert environment["HOME"] == home
    assert not {"XDG_CONFIG_HOME", "XDG_DATA_HOME", "CONTAINERS_STORAGE_CONF"} & environment.keys()
    paths = peer._engine_storage_override_paths(UID, home)
    assert {str(p) for p in paths if ".config/containers" in str(p)} == {
        home + "/.config/containers/storage.conf",
        home + "/.config/containers/storage.conf.d",
    }
    locks = peer._engine_lock_specs(UID, home)
    assert [str(p) for p, _ in locks[:2]] == [
        home + "/.local/share/containers/storage/overlay-images/images.lock",
        home + "/.local/share/containers/storage/overlay-layers/layers.lock",
    ]
    assert [size for _, size in locks] == [64, 64, 0, 64]
    assert all(str(p).startswith("/run/user/983/") for p, _ in locks[2:])


@pytest.mark.parametrize(
    "home", ["/tmp/hfcache", "/var/lib/hfcache/../root", CONTAINER + "/", True, 1]
)
def test_unknown_alias_or_coerced_home_refuses_before_passwd_or_path_work(home, monkeypatch):
    monkeypatch.setattr(peer.pwd, "getpwnam", lambda _: pytest.fail("untrusted home used"))
    with pytest.raises(peer.PeerError):
        peer._account_home(indexed_account(home))


@pytest.mark.parametrize("change", ["home", "uid", "gid"])
def test_account_drift_refuses_bound_home_without_trying_other_store(change, monkeypatch):
    account = SimpleNamespace(pw_uid=UID, pw_gid=GID, pw_dir=CONTAINER)
    setattr(
        account,
        {"home": "pw_dir", "uid": "pw_uid", "gid": "pw_gid"}[change],
        DEFAULT if change == "home" else UID + 1,
    )
    monkeypatch.setattr(peer.pwd, "getpwnam", lambda _: account)
    with pytest.raises(peer.PeerError):
        peer._account_home(indexed_account(CONTAINER))


def test_missing_field_preserves_default_and_native_never_accepts_rootless_home(monkeypatch):
    account = SimpleNamespace(pw_uid=UID, pw_gid=GID, pw_dir=DEFAULT)
    monkeypatch.setattr(peer.pwd, "getpwnam", lambda _: account)
    assert peer._account_home(indexed_account()) == DEFAULT
    account.pw_dir = CONTAINER
    with pytest.raises(peer.PeerError):
        peer._account_home(indexed_account())
    with pytest.raises(peer.PeerError):
        peer._account_home(indexed_account(CONTAINER, profile="native"))


def test_rootless_index_binds_closed_home(rootless):
    for home in (DEFAULT, CONTAINER):
        value = deepcopy(rootless.index)
        value["profile_evidence"]["account_home"] = home
        assert policy._deployment(json.dumps(value).encode()) == value


def test_native_index_rejects_rootless_account_home_field(native):
    value = deepcopy(native.index)
    value["profile_evidence"]["account_home"] = CONTAINER
    with pytest.raises(policy.InspectionError):
        policy._deployment(json.dumps(value).encode())


def test_owned_alternate_override_capture_never_reads_default_home(storage):
    # The unselected home's present override would fail if fallback were tried.
    unselected = storage.root / "var/lib/hfcache/.config/containers/storage.conf"
    unselected.parent.mkdir(parents=True)
    unselected.write_bytes(b"unsupported unselected configuration")
    result = peer._engine_storage_config(UID, GID, engine_budget(), CONTAINER)
    assert len(result["overrides"]) == 9
    selected = storage.root / "var/lib/hfcache/container-home/.config/containers/storage.conf"
    selected.parent.mkdir(parents=True)
    selected.write_bytes(b"")
    with pytest.raises(peer.PeerError):
        peer._engine_storage_config(UID, GID, engine_budget(), CONTAINER)
    assert storage.opened == set()


def test_owned_alternate_lock_capture_keeps_exact_labels_sizes_and_nofollow(locks):
    base = locks.root / "var/lib/hfcache"
    home = base / "container-home"
    home.mkdir(mode=0o700)
    (base / ".local").rename(home / ".local")
    locks.runtime_inodes.add(home.stat().st_ino)
    rows = peer._engine_storage_locks(UID, GID, lock_budget(), CONTAINER)
    assert [row["identity"]["bytes"] for row in rows] == [64, 64, 0, 64]
    assert [row["path"] for row in rows[:2]] == [
        str(p) for p, _ in peer._engine_lock_specs(UID, CONTAINER)[:2]
    ]
    leaf = locks.root / Path(rows[0]["path"]).relative_to("/")
    locks.original.setxattr(leaf, "user.web006_context", b"x:object_r:container_file_t:s0")
    with pytest.raises(peer.PeerError):
        peer._engine_storage_locks(UID, GID, lock_budget(), CONTAINER)
    assert not locks.opened


@pytest.mark.parametrize("kind", ["missing", "symlink"])
def test_selected_alternate_lock_failure_never_falls_back_to_valid_default_locks(locks, kind):
    base = locks.root / "var/lib/hfcache"
    before = [(p.stat().st_ino, p.read_bytes()) for p in locks.leaves]
    if kind == "symlink":
        (base / "container-home").symlink_to(base, target_is_directory=True)
    with pytest.raises((peer.PeerError, OSError)):
        peer._engine_storage_locks(UID, GID, lock_budget(), CONTAINER)
    assert before == [(p.stat().st_ino, p.read_bytes()) for p in locks.leaves]
    assert not locks.opened


def test_final_snapshot_validation_rejects_passwd_home_drift(rootless, monkeypatch):
    snapshot = policy.inspect_authority()
    principal = rootless.index["api_principal"]
    account = SimpleNamespace(
        pw_uid=principal["host_uid"], pw_gid=principal["host_gid"], pw_dir=CONTAINER
    )
    monkeypatch.setattr(policy.pwd, "getpwnam", lambda _: account)
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


def test_original_parent_peer_proof_rechecks_home_after_owned_child(monkeypatch):
    principal = {"host_uid": os.getuid(), "host_gid": os.getgid()}
    source = {
        "profile": "rootless",
        "api_principal": principal,
        "profile_evidence": {"account_home": CONTAINER},
    }
    snapshot = cast(
        "policy.AuthoritySnapshot",
        SimpleNamespace(
            api_principal=tuple(principal.values()),
            budget=policy.InspectionBudget(),
            deployment_sha256="a" * 64,
            profile="rootless",
            deployment=source,
        ),
    )
    account = SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid(), pw_dir=CONTAINER)
    monkeypatch.setattr(peer.pwd, "getpwnam", lambda _: account)
    value = {
        "schema_version": 1,
        "deployment_sha256": "a" * 64,
        "profile": "rootless",
        "process": {
            "pid": os.getpid(),
            "start_ticks": 12345,
            "credentials": {"Uid": [os.getuid()] * 4, "Gid": [os.getgid()] * 4},
            "security": {
                "NoNewPrivs": "1",
                "Seccomp": "2",
                "CapEff": "0",
                "CapBnd": "0",
                "CapPrm": "0",
                "CapAmb": "0",
            },
        },
        "manager": {"InvocationID": "b" * 32},
        "container": {},
        "work": {"files": 1, "bytes": 64},
    }
    observations = []
    change_after_observation = [False]

    def observed(*_args, **kwargs):
        assert kwargs["home"] == CONTAINER
        observations.append(True)
        if change_after_observation[0]:
            account.pw_dir = DEFAULT
        return json.dumps(value).encode()

    monkeypatch.setattr(peer, "_observe_as_account", observed)
    first, second = socket.socketpair()
    try:
        original = LivePeer(first)
        try:
            proof = peer.authenticate(snapshot, original, remaining_seconds=1)
            assert proof.profile == "rootless"
            assert len(observations) == 1
            change_after_observation[0] = True
            with pytest.raises(peer.PeerError):
                peer.authenticate(snapshot, original, remaining_seconds=1)
            assert len(observations) == 2
        finally:
            original.close()
    finally:
        first.close()
        second.close()


def test_helper_masks_both_exact_secret_roots_without_granting_a_home_tree():
    text = (Path(__file__).parents[2] / "packaging/systemd/hfcache-host-helper.service").read_text()
    masks = {
        part
        for line in text.splitlines()
        if line.startswith("InaccessiblePaths=")
        for part in line.partition("=")[2].split()
    }
    writable = {
        part
        for line in text.splitlines()
        if line.startswith("ReadWritePaths=")
        for part in line.partition("=")[2].split()
    }
    for home in (DEFAULT, CONTAINER):
        assert "-" + home + "/.local/share/containers/storage/secrets" in masks
        assert "-" + home + "/.local/share/containers" in writable
        assert home not in writable
        assert "-" + home not in writable
    assert "CapabilityBoundingSet=CAP_SETUID CAP_SETGID" in text
    assert "RestrictNamespaces=user" in text
