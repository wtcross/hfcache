"""Exact stock vendor bundle tests using real owned files and modeled root IDs.

No namespace, capability, guest, package-manager or engine action runs here.
"""

import hashlib
import json
import os
import time
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from hfcache import host_peer as module

UID = GID = 983
BUNDLES: list[dict[str, Any]] = [
    {
        "path": "/usr/share/containers/storage.conf.d",
        "entries": [
            {
                "name": "00-vendor.conf",
                "bytes": 29,
                "content": '[storage]\ndriver = "overlay"\n',
                "sha256": "358b7ba3201aea7dba1d8e0e42c8a11e21acdff1b2ca71a4f8b826f41ae5bc80",
            }
        ],
    },
    {
        "path": "/usr/share/containers/storage.rootless.conf.d",
        "entries": [
            {
                "name": "00-vendor-rootless.conf",
                "bytes": 186,
                "content": (
                    "[storage.options.overlay]\n"
                    "# mountopt specifies comma separated list of extra mount options\n"
                    "# Note unlike the rootful config we cannot use metacopy=on as rootless user\n"
                    'mountopt = "nodev"\n'
                ),
                "sha256": "f346071a81b5fdb96796397b08f9dc40c9f450166c7f041ddcaa92f115e92ca8",
            }
        ],
    },
]
VENDOR_PATHS = [item["path"] for item in BUNDLES]


def budget(files=1024, size=64 * 1024 * 1024, seconds=5):
    return module._Budget(time.monotonic() + seconds, files, size)


def modeled_root(info):
    return SimpleNamespace(
        **{
            name: 0 if name in {"st_uid", "st_gid"} else getattr(info, name)
            for name in dir(info)
            if name.startswith("st_")
        }
    )


@pytest.fixture
def storage(tmp_path, monkeypatch):
    root = tmp_path / "owned-root"
    root.mkdir()
    stock = root / "usr/share/containers/storage.conf"
    stock.parent.mkdir(parents=True)
    body = b'[storage.options.overlay]\nmountopt = "nodev"\n'
    stock.write_bytes(body)
    stock.chmod(0o644)
    for bundle in BUNDLES:
        directory = root / bundle["path"].removeprefix("/")
        directory.mkdir(mode=0o755)
        directory.chmod(0o755)
        for entry in bundle["entries"]:
            leaf = directory / entry["name"]
            leaf.write_bytes(entry["content"].encode())
            leaf.chmod(0o644)
    original = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    proxy = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    opened = set()
    events = []

    def open_owned(path, flags, *args, **kwargs):
        descriptor = original.open(root if path == "/" else path, flags, *args, **kwargs)
        opened.add(descriptor)
        events.append((str(path), flags))
        return descriptor

    def close_owned(descriptor):
        opened.remove(descriptor)
        return original.close(descriptor)

    proxy.open, proxy.close = open_owned, close_owned
    proxy.fstat = lambda descriptor: modeled_root(original.fstat(descriptor))
    proxy.stat = lambda *args, **kwargs: modeled_root(original.stat(*args, **kwargs))
    proxy.getresuid = lambda: (UID,) * 3
    proxy.getresgid = lambda: (GID,) * 3
    proxy.getgroups = list
    monkeypatch.setattr(module, "os", proxy)
    monkeypatch.setattr(module, "_ENGINE_STORAGE_CONFIG_SHA", hashlib.sha256(body).hexdigest())
    yield SimpleNamespace(
        root=root,
        stock=stock,
        body=body,
        original=original,
        proxy=proxy,
        opened=opened,
        events=events,
    )
    assert not opened


def leaf_path(storage, index):
    bundle = BUNDLES[index]
    return storage.root / bundle["path"].removeprefix("/") / bundle["entries"][0]["name"]


def test_fixed_public_vendor_bytes_and_semantics_match_the_supported_bundle():
    assert len(module._ENGINE_STORAGE_VENDOR_DROPINS) == 2
    for bundle in BUNDLES:
        (entry,) = bundle["entries"]
        body = entry["content"].encode()
        assert len(body) == entry["bytes"]
        assert hashlib.sha256(body).hexdigest() == entry["sha256"]
        assert module._ENGINE_STORAGE_VENDOR_DROPINS[Path(bundle["path"])] == (
            entry["name"],
            len(body),
            hashlib.sha256(body).hexdigest(),
        )
    assert tomllib.loads(BUNDLES[0]["entries"][0]["content"]) == {"storage": {"driver": "overlay"}}
    assert tomllib.loads(BUNDLES[1]["entries"][0]["content"]) == {
        "storage": {"options": {"overlay": {"mountopt": "nodev"}}}
    }


def test_full_fresh_proof_records_both_closed_bundles_and_shared_budget(storage):
    work = budget()
    first = module._engine_storage_config(UID, GID, work)
    assert first == module._engine_storage_config(UID, GID, budget())
    assert json.loads(json.dumps(first)) == first
    assert first["original_options"] == ["overlay.mountopt=nodev"]
    stock_rows = [row for row in first["overrides"] if row["state"] == "stock-directory"]
    assert {row["path"] for row in stock_rows} == set(VENDOR_PATHS)
    assert all(set(row) == {"path", "state", "identity", "entries"} for row in stock_rows)
    assert all(len(row["entries"]) == 1 for row in stock_rows)
    assert len([row for row in first["overrides"] if row["state"] == "absent"]) == 7
    assert work.files == 12
    assert work.bytes == len(storage.body) + 29 + 186
    assert not storage.opened


@pytest.mark.parametrize(
    "path",
    [
        str(path)
        for path in module._engine_storage_override_paths(UID)
        if str(path) not in VENDOR_PATHS
    ],
)
def test_each_other_effective_override_still_refuses_even_empty(storage, path):
    target = storage.root / path.removeprefix("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.endswith("storage.conf"):
        target.write_bytes(b"")
    else:
        target.mkdir()
    with pytest.raises((module.PeerError, OSError)):
        module._engine_storage_config(UID, GID, budget())


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize(
    "kind",
    [
        "absent-directory",
        "empty-directory",
        "extra-file",
        "extra-hidden",
        "extra-subdir",
        "leaf-symlink",
        "directory-symlink",
        "hardlink",
        "fifo",
        "mode",
        "wrong-digest",
        "short",
        "oversize",
    ],
)
def test_vendor_allowlist_never_accepts_other_stock_or_custom_shapes(storage, index, kind):
    leaf = leaf_path(storage, index)
    directory = leaf.parent
    if kind == "absent-directory":
        leaf.unlink()
        directory.rmdir()
    elif kind == "empty-directory":
        leaf.unlink()
    elif kind in {"extra-file", "extra-hidden"}:
        name = "99-custom.conf" if kind == "extra-file" else ".unknown"
        (directory / name).write_bytes(b"custom")
    elif kind == "extra-subdir":
        (directory / "983").mkdir()
    elif kind == "leaf-symlink":
        other = directory.with_name("owned-outside")
        other.write_bytes(leaf.read_bytes())
        leaf.unlink()
        leaf.symlink_to(other)
    elif kind == "directory-symlink":
        outside = directory.with_name("owned-outside")
        directory.rename(outside)
        directory.symlink_to(outside, target_is_directory=True)
    elif kind == "hardlink":
        os.link(leaf, directory.with_name("other-hardlink"))
    elif kind == "fifo":
        leaf.unlink()
        os.mkfifo(leaf, 0o644)
    elif kind == "mode":
        leaf.chmod(0o664)
    elif kind == "wrong-digest":
        leaf.write_bytes(b"x" * leaf.stat().st_size)
    elif kind == "short":
        leaf.write_bytes(b"x")
    elif kind == "oversize":
        leaf.write_bytes(b"x" * 65537)
    with pytest.raises((module.PeerError, OSError)):
        module._engine_storage_config(UID, GID, budget())


@pytest.mark.parametrize("target_kind", ["directory", "leaf", "ancestor"])
@pytest.mark.parametrize("change", ["uid", "gid", "writable"])
def test_vendor_root_ownership_and_ancestors_are_required(storage, target_kind, change):
    leaf = leaf_path(storage, 0)
    path = (
        leaf
        if target_kind == "leaf"
        else leaf.parent
        if target_kind == "directory"
        else leaf.parent.parent
    )
    inode = path.stat().st_ino
    original = storage.proxy.fstat

    def altered(descriptor):
        info = original(descriptor)
        if info.st_ino == inode:
            if change == "uid":
                info.st_uid = UID
            elif change == "gid":
                info.st_gid = GID
            else:
                info.st_mode |= 0o020
        return info

    storage.proxy.fstat = altered
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, budget())


@pytest.mark.parametrize("change", ["replace-leaf", "add-entry", "replace-directory"])
def test_real_midread_identity_or_entry_changes_cannot_publish_a_stock_proof(storage, change):
    leaf = leaf_path(storage, 0)
    inode = leaf.stat().st_ino
    changed = False

    def read(descriptor, maximum):
        nonlocal changed
        body = storage.original.read(descriptor, maximum)
        if body and not changed and storage.original.fstat(descriptor).st_ino == inode:
            changed = True
            if change == "replace-leaf":
                replacement = leaf.with_name("replacement")
                replacement.write_bytes(body)
                replacement.chmod(0o644)
                replacement.replace(leaf)
            elif change == "add-entry":
                (leaf.parent / "99-custom.conf").write_bytes(b"custom")
            else:
                parent = leaf.parent
                parent.rename(parent.with_name("retained-old"))
                parent.mkdir(mode=0o755)
                leaf.write_bytes(body)
                leaf.chmod(0o644)
        return body

    storage.proxy.read = read
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, budget())
    assert changed


@pytest.mark.parametrize(
    "work", [lambda: budget(files=11), lambda: budget(size=215), lambda: budget(seconds=-1)]
)
def test_original_file_byte_time_budgets_are_shared_not_reset(storage, work):
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, work())


def test_no_unlisted_vendor_path_can_select_a_directory(storage):
    with pytest.raises(module.PeerError):
        module._engine_storage_vendor_directory(Path("/usr/share/containers/arbitrary"), budget())
    assert storage.events == []
