"""Root-receipt and fixed label metadata tests; actual MAC denial is guest-owned."""

import copy
import errno
import json
import os
from pathlib import Path
from typing import Any

import pytest

from hfcache import host_policy as policy


def receipt() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "module": {
            "name": "hfcache_host_helper",
            "version": 1,
            "priority": 400,
            "source_sha256": "a" * 64,
            "loaded_sha256": "b" * 64,
        },
        "domain": policy.SELINUX_CONTEXT,
        "kernel_policy_sha256": "c" * 64,
        "labels": {**policy.SELINUX_LABELS, "archive": "nfs_t"},
    }


def parse(value):
    return policy._selinux_installation(json.dumps(value).encode(), "a" * 64)


@pytest.mark.parametrize("archive", ["nfs_t", "hfcache_archive_t"])
def test_closed_root_receipt_accepts_only_documented_archive_roles(archive):
    value = receipt()
    value["labels"]["archive"] = archive
    assert parse(value) == value
    # The loaded/kernel digests attest independent provisioning, rather than
    # pretending this parser queried the running kernel or loaded a module.
    assert value["module"]["loaded_sha256"] != value["module"]["source_sha256"]


@pytest.mark.parametrize(
    ("role", "wrong_type"),
    [
        ("configuration", "hfcache_host_helper_application_conf_t"),
        ("application_config", "hfcache_host_helper_conf_t"),
        ("hub_home", "hfcache_host_helper_secret_t"),
        ("hub_cache", "hfcache_host_helper_secret_t"),
        ("api_credentials", "hfcache_host_helper_hub_state_t"),
        ("container_secrets", "hfcache_host_helper_hub_state_t"),
    ],
)
def test_shared_inputs_cannot_relabel_private_authority_or_readonly_credentials(role, wrong_type):
    value = receipt()
    value["labels"][role] = wrong_type
    with pytest.raises(policy.InspectionError):
        parse(value)


def test_application_configuration_label_role_is_required_independently():
    value = receipt()
    del value["labels"]["application_config"]
    with pytest.raises(policy.InspectionError):
        parse(value)


@pytest.mark.parametrize(
    "change",
    [
        "extra",
        "missing",
        "schema_bool",
        "schema_other",
        "domain",
        "domain_suffix",
        "module_extra",
        "module_missing",
        "module_name",
        "version_bool",
        "version_other",
        "priority_bool",
        "priority_other",
        "source",
        "source_upper",
        "loaded",
        "kernel",
        "label_extra",
        "label_missing",
        "archive",
        "secret",
        "code",
        "path_selector",
    ],
)
def test_unbound_or_broader_receipt_cannot_manufacture_authority(change):  # noqa: PLR0912 - closed adversary matrix
    value = copy.deepcopy(receipt())
    if change == "extra":
        value["effect"] = "permit"
    elif change == "missing":
        del value["labels"]
    elif change == "schema_bool":
        value["schema_version"] = True
    elif change == "schema_other":
        value["schema_version"] = 2
    elif change == "domain":
        value["domain"] = "system_u:system_r:unconfined_t:s0"
    elif change == "domain_suffix":
        value["domain"] += ":c0"
    elif change == "module_extra":
        value["module"]["path"] = "/custom/module"
    elif change == "module_missing":
        del value["module"]["loaded_sha256"]
    elif change == "module_name":
        value["module"]["name"] = "other"
    elif change == "version_bool":
        value["module"]["version"] = True
    elif change == "version_other":
        value["module"]["version"] = 2
    elif change == "priority_bool":
        value["module"]["priority"] = True
    elif change == "priority_other":
        value["module"]["priority"] = 100
    elif change == "source":
        value["module"]["source_sha256"] = "d" * 64
    elif change == "source_upper":
        value["module"]["source_sha256"] = "A" * 64
    elif change == "loaded":
        value["module"]["loaded_sha256"] = "bad"
    elif change == "kernel":
        value["kernel_policy_sha256"] = "bad"
    elif change == "label_extra":
        value["labels"]["arbitrary"] = "etc_t"
    elif change == "label_missing":
        del value["labels"]["hub_home"]
    elif change == "archive":
        value["labels"]["archive"] = "usr_t"
    elif change == "secret":
        value["labels"]["container_secrets"] = "container_file_t"
    elif change == "code":
        value["labels"]["helper_code"] = "usr_t"
    else:
        value["labels"]["archive"] = {"path": "/any", "type": "nfs_t"}
    with pytest.raises((ValueError, TypeError)):
        parse(value)


def test_duplicate_keys_and_oversized_receipts_refuse():
    body = json.dumps(receipt()).encode()
    duplicate = body.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1')
    for raw in (duplicate, body + b" " * policy.MAX_SELINUX_INSTALLATION):
        with pytest.raises(policy.InspectionError):
            policy._selinux_installation(raw, "a" * 64)


@pytest.mark.parametrize(
    "context",
    [
        policy.SELINUX_CONTEXT.encode(),
        policy.SELINUX_CONTEXT.encode() + b"\0",
        policy.SELINUX_CONTEXT.encode() + b"\n",
    ],
)
def test_kernel_state_uses_fixed_paths_bounded_reads_and_charges_real_bytes(
    tmp_path, monkeypatch, context
):
    enforce = tmp_path / "enforce"
    current = tmp_path / "current"
    enforce.write_bytes(b"1\n")
    current.write_bytes(context)
    original = os.open
    opened = []
    paths = {"/sys/fs/selinux/enforce": enforce, f"/proc/{os.getpid()}/attr/current": current}

    def fixed(path, flags):
        assert str(path) in paths
        assert flags & os.O_NOFOLLOW
        assert flags & os.O_NONBLOCK
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        fd = original(paths[str(path)], flags)
        opened.append(fd)
        return fd

    monkeypatch.setattr(os, "open", fixed)
    budget = policy.InspectionBudget()
    policy._selinux_state(budget)
    assert budget.files == 2
    assert budget.bytes == len(context) + 2
    for fd in opened:
        with pytest.raises(OSError, match="Bad file descriptor") as error:
            os.fstat(fd)
        assert error.value.errno == errno.EBADF


@pytest.mark.parametrize(
    ("enforce", "context"),
    [
        (b"0", policy.SELINUX_CONTEXT.encode()),
        (b"1", b"unconfined_u:unconfined_r:unconfined_t:s0\0"),
        (b"1", policy.SELINUX_CONTEXT.encode() + b"\0\0"),
        (b"1", policy.SELINUX_CONTEXT.encode() + b" "),
    ],
)
def test_wrong_kernel_state_refuses_with_actual_file_descriptors_closed(
    tmp_path, monkeypatch, enforce, context
):
    files = [tmp_path / "enforce", tmp_path / "current"]
    for path, body in zip(files, (enforce, context), strict=True):
        path.write_bytes(body)
    original = os.open
    opened = []

    def fixed(path, flags):
        target = files[0] if str(path) == "/sys/fs/selinux/enforce" else files[1]
        fd = original(target, flags)
        opened.append(fd)
        return fd

    monkeypatch.setattr(os, "open", fixed)
    with pytest.raises(policy.InspectionError):
        policy._selinux_state(policy.InspectionBudget())
    for fd in opened:
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(fd)


@pytest.fixture
def labelled(tmp_path, monkeypatch):
    path = tmp_path / "code.py"
    path.write_bytes(b"owned unit metadata; no secrets")
    label = b"system_u:object_r:hfcache_host_helper_code_t:s0\0"
    os.setxattr(path, "user.web006_label", label)
    original = os.getxattr

    def model(path, name, *, follow_symlinks):
        assert name == "security.selinux"
        assert follow_symlinks is False
        return original(path, "user.web006_label", follow_symlinks=False)

    monkeypatch.setattr(os, "getxattr", model)
    monkeypatch.setattr(policy, "OWNER", os.geteuid())
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = [(Path("/"), "ext4", {"rw"}, {"rw"})]
    return path, capture


def test_label_metadata_revalidates_inode_and_context_without_reading_body(labelled, monkeypatch):
    path, capture = labelled
    original = os.open

    def directory_only(path, flags, **kwargs):
        assert flags & os.O_DIRECTORY  # the body is never opened
        return original(path, flags, **kwargs)

    monkeypatch.setattr(os, "open", directory_only)
    capture.label(path, policy.SELINUX_LABELS["helper_code"])
    capture.revalidate()
    assert len(capture.labels) == 1


@pytest.mark.parametrize("change", ["label", "inode", "symlink", "writable"])
def test_label_drift_and_alias_replacement_refuse(labelled, change):
    path, capture = labelled
    capture.label(path, policy.SELINUX_LABELS["helper_code"])
    if change == "label":
        os.setxattr(path, "user.web006_label", b"system_u:object_r:usr_t:s0\0")
    elif change == "inode":
        replacement = path.with_name("replacement.py")
        replacement.write_bytes(path.read_bytes())
        os.setxattr(
            replacement, "user.web006_label", b"system_u:object_r:hfcache_host_helper_code_t:s0\0"
        )
        replacement.replace(path)
    elif change == "symlink":
        other = path.with_name("other.py")
        path.rename(other)
        path.symlink_to(other)
    else:
        path.chmod(0o666)
    with pytest.raises((ValueError, OSError)):
        capture.revalidate()
