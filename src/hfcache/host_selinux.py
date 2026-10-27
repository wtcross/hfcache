"""Optional fixed host-effect labels; standard-library protected bootstrap only.

Receipt version1 remains the read/configuration provisioning contract. Version2
adds exact native host-effect roles, never a policy grant or a path selector.
"""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

HOST_ACTION_LABELS = {
    "schedule_directory": "hfcache_host_helper_schedule_dir_t",
    "schedule_file": "hfcache_host_helper_schedule_file_t",
    "host_action_state": "hfcache_host_helper_host_action_state_t",
    "sync_timer_unit": "hfcache_host_helper_sync_timer_unit_t",
}
OBSERVER_STATE_TYPE = "hfcache_sync_observer_state_t"
SYNC_OBSERVER_STATE = Path("/var/lib/hfcache/scheduled/sync")
OBSERVER_STATE_MODE = 0o700
SCHEDULE_DIRECTORY = Path("/etc/systemd/system/hfcache-sync.timer.d")
SCHEDULE = SCHEDULE_DIRECTORY / "50-cockpit.conf"
SCHEDULE_HISTORY = SCHEDULE_DIRECTORY / ".hfcache-actions"
HOST_ACTION_STATE = Path("/etc/hfcache/.host-actions")
OWNER = 0
OWNER_GID = 0
READ_RECEIPT_VERSION = 1
HOST_EFFECT_RECEIPT_VERSION = 2
MANAGED_FILE_MODE = 0o644
LEGACY_POLICY = Path("/etc/hfcache/cockpit-policy.json")
MAX_LEGACY_POLICY_BYTES = 4096
LEGACY_ACTIONS = frozenset({"archive", "hub", "control", "schedule", "configuration", "observer"})


def legacy_host_actions_disabled(
    inspection: Any,  # noqa: ANN401 - same protected capture ABI, no package imports
    need: Callable[[object], None],
) -> None:
    """Exclude optional legacy host controls, without migrating their authority.

    Current bytes cannot prove that an older privileged call already drained.
    Explicit quiescent activation remains an independent operator prerequisite.
    """
    capture = inspection.capture
    capture.budget.consume(files=1)
    parent = capture.parent(LEGACY_POLICY)
    try:
        try:
            os.stat(LEGACY_POLICY.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            need(LEGACY_POLICY not in capture.files)
            capture.absent.add(LEGACY_POLICY)
            return
        need(LEGACY_POLICY not in capture.absent)
    finally:
        os.close(parent)
    raw = capture.read(LEGACY_POLICY, maximum=MAX_LEGACY_POLICY_BYTES, mode=None)

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            need(key not in result)
            result[key] = value
        return result

    def invalid(_value: str) -> None:
        need(False)  # noqa: FBT003 - fixed nonfinite refusal

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError):
        need(False)  # noqa: FBT003 - fixed malformed receipt refusal
        return
    need(type(value) is dict)
    need(set(value) == {"schema_version", "source_commit", "index_sha256", "permissions"})
    need(type(value["schema_version"]) is int and value["schema_version"] == READ_RECEIPT_VERSION)
    need(
        type(value["source_commit"]) is str
        and re.fullmatch(r"[0-9a-f]{40}", value["source_commit"]) is not None
    )
    need(
        type(value["index_sha256"]) is str
        and re.fullmatch(r"[0-9a-f]{64}", value["index_sha256"]) is not None
    )
    permissions = value["permissions"]
    need(type(permissions) is dict and set(permissions) == LEGACY_ACTIONS)
    need(all(type(permission) is bool for permission in permissions.values()))
    need(permissions["schedule"] is False and permissions["observer"] is False)


def installation_labels(
    version: object,
    labels: object,
    base_labels: Mapping[str, str],
    need: Callable[[object], None],
) -> dict[str, str]:
    """Validate one closed receipt version without widening legacy authority."""
    need(type(version) is int and version in {READ_RECEIPT_VERSION, HOST_EFFECT_RECEIPT_VERSION})
    expected = dict(base_labels)
    if version == HOST_EFFECT_RECEIPT_VERSION:
        expected.update(HOST_ACTION_LABELS)
    need(type(labels) is dict)
    values = cast("dict[str, str]", labels)
    roles = {*expected, "archive"}
    observer_roles = roles | {"observer_state"}
    need(
        set(values) == roles
        or (version == HOST_EFFECT_RECEIPT_VERSION and set(values) == observer_roles)
    )
    need(all(values[role] == value for role, value in expected.items()))
    if "observer_state" in values:
        need(values["observer_state"] == OBSERVER_STATE_TYPE)
    need(type(values["archive"]) is str and values["archive"] in {"nfs_t", "hfcache_archive_t"})
    return values


def observer_state_labels(
    inspection: Any,  # noqa: ANN401 - trusted protected capture ABI
    receipt: Mapping[str, Any],
    need: Callable[[object], None],
) -> None:
    """Require the optional SDK state label without reading retained handles.

    Schedule authority does not call this proof. The service account comes from
    the independently validated native deployment, never an incoming request.
    """
    need(inspection.deployment["profile"] == "native")
    need(
        type(receipt["schema_version"]) is int
        and receipt["schema_version"] == HOST_EFFECT_RECEIPT_VERSION
    )
    need(receipt["labels"].get("observer_state") == OBSERVER_STATE_TYPE)
    account = inspection.deployment["api_principal"]
    uid, gid = account["host_uid"], account["host_gid"]
    need(type(uid) is int and type(gid) is int and uid > 0 and gid > 0)
    inspection.capture.label(SYNC_OBSERVER_STATE, OBSERVER_STATE_TYPE, owner=(uid, gid))
    inspection.capture.budget.consume(files=1)
    info = SYNC_OBSERVER_STATE.lstat()
    need(stat.S_ISDIR(info.st_mode))
    need(
        info.st_uid == uid
        and info.st_gid == gid
        and stat.S_IMODE(info.st_mode) == OBSERVER_STATE_MODE
    )


def host_action_labels(
    inspection: Any,  # noqa: ANN401 - protected capture ABI avoids application package imports
    receipt: Mapping[str, Any],
    need: Callable[[object], None],
) -> None:
    """Pin only the fixed native effect objects under the original read budget.

    This does not inspect a user manager, create state or grant an effect. The
    caller separately proves the receipt/index/policy and original guard inodes.
    Mutable fixed directories retain stable parent identity and their full SID;
    immutable unit/managed leaves retain complete descriptor metadata.
    """
    need(inspection.deployment["profile"] == "native")
    need(
        type(receipt["schema_version"]) is int
        and receipt["schema_version"] == HOST_EFFECT_RECEIPT_VERSION
    )
    labels = receipt["labels"]
    need(all(labels.get(role) == value for role, value in HOST_ACTION_LABELS.items()))
    legacy_host_actions_disabled(inspection, need)
    objects = (
        (SCHEDULE_DIRECTORY, "schedule_directory", 0o755, True),
        (SCHEDULE_HISTORY, "host_action_state", 0o700, True),
        (HOST_ACTION_STATE, "host_action_state", 0o700, True),
        (
            inspection.selected / "packaging/systemd/hfcache-sync.timer",
            "sync_timer_unit",
            MANAGED_FILE_MODE,
            False,
        ),
    )
    for path, role, mode, directory in objects:
        inspection.capture.label(path, HOST_ACTION_LABELS[role])
        inspection.capture.budget.consume(files=1)
        info = path.lstat()
        need(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
        need(
            info.st_uid == OWNER and info.st_gid == OWNER_GID and stat.S_IMODE(info.st_mode) == mode
        )
        if not directory:
            need(info.st_nlink == 1)
    inspection.capture.budget.consume(files=1)
    try:
        info = SCHEDULE.lstat()
    except FileNotFoundError:
        return
    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
    need(
        info.st_uid == OWNER
        and info.st_gid == OWNER_GID
        and stat.S_IMODE(info.st_mode) == MANAGED_FILE_MODE
    )
    inspection.capture.label(SCHEDULE, HOST_ACTION_LABELS["schedule_file"])
