"""Strict nonsecret host-status authority (INV-003/013/014, decision150).

The helper reports administrative evidence, never archive health or operation
completion. Unknown authority cannot carry partial permissions.
"""

import re
from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, ConfigDict, Field, model_validator

from hfcache.models import ArchiveIdField, CommitShaField, DurableModel, Sha256

_ASCII_SPACE = 32
_ASCII_TILDE = 126


def _one(value: object) -> int:
    if type(value) is not int or value != 1:
        message = "host schema version must be integer1"
        raise ValueError(message)
    return value


def _version(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9][A-Za-z0-9.+-]*", value) is None:
        message = "host release version is invalid"
        raise ValueError(message)
    return value


HostSchemaOne = Annotated[Literal[1], BeforeValidator(_one)]
HostProfile = Literal["native", "rootless"]
HostAction = Literal["archive", "hub", "control", "schedule", "configuration", "observer"]
HOST_ACTIONS = ("archive", "hub", "control", "schedule", "configuration", "observer")
HostReason = Literal[
    "helper-disabled",
    "helper-unavailable",
    "helper-timeout",
    "helper-refused",
    "helper-busy",
    "policy-missing",
    "policy-invalid",
    "deployment-unverified",
    "facts-unavailable",
    "guard-unconfirmed",
    "key-missing",
    "key-invalid",
    "config-unavailable",
]
HostPermissionReason = Literal[
    "granted",
    "policy-denied",
    "guard-held",
    "profile-unproved",
    "authority-unknown",
    "helper-unavailable",
]
HostUnitName = Literal[
    "hfcache-sync.service",
    "hfcache-verify.service",
    "hfcache-sync.timer",
    "hfcache-verify.timer",
]
HOST_UNITS = (
    "hfcache-sync.service",
    "hfcache-verify.service",
    "hfcache-sync.timer",
    "hfcache-verify.timer",
)


class HostModel(DurableModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class HostBinding(HostModel):
    deployment_sha256: Sha256
    policy_sha256: Sha256
    release_version: Annotated[str, BeforeValidator(_version), Field(max_length=128)]
    source_commit: CommitShaField
    source_snapshot_sha256: Sha256
    source_dirty: bool
    archive_id: ArchiveIdField
    archive_root: Literal["/srv/hfcache"]


class HostPermissions(HostModel):
    archive: bool
    hub: bool
    control: bool
    schedule: bool
    configuration: bool
    observer: bool


class HostPermissionReasons(HostModel):
    archive: HostPermissionReason
    hub: HostPermissionReason
    control: HostPermissionReason
    schedule: HostPermissionReason
    configuration: HostPermissionReason
    observer: HostPermissionReason


class HostUnitState(HostModel):
    load: Literal["loaded", "masked", "not-found"]
    active: Literal["active", "inactive", "failed"]
    unit_file: Literal[
        "enabled",
        "enabled-runtime",
        "disabled",
        "static",
        "linked",
        "linked-runtime",
        "masked",
        "masked-runtime",
        "not-found",
    ]


class HostSyncSchedule(HostModel):
    state: Literal["observed", "unavailable"]
    reason: Literal["profile-unproved", "facts-unavailable"] | None
    revision: Sha256 | None
    source: Literal["default", "managed"] | None
    on_calendar: Annotated[str, Field(min_length=1, max_length=4096)] | None
    randomized_delay_sec: Annotated[str, Field(min_length=1, max_length=256)] | None

    @model_validator(mode="after")
    def complete_schedule(self) -> Self:
        required = (self.revision, self.source, self.on_calendar)
        all_values = (*required, self.randomized_delay_sec)
        if (
            self.state == "observed"
            and (self.reason is not None or any(x is None for x in required))
        ) or (
            self.state == "unavailable"
            and (self.reason is None or any(x is not None for x in all_values))
        ):
            message = "host schedule state and evidence disagree"
            raise ValueError(message)
        for value in (self.on_calendar, self.randomized_delay_sec):
            if value is not None and any(not _ASCII_SPACE <= ord(c) <= _ASCII_TILDE for c in value):
                message = "host schedule values must be bounded printable ASCII"
                raise ValueError(message)
        return self


class HostFacts(HostModel):
    guard: Literal["held", "absent", "inactive"]
    archive_mount: Literal["nfs-ro", "nfs-rw", "local-ro", "local-rw", "absent"]
    units: dict[HostUnitName, HostUnitState]
    sync_schedule: HostSyncSchedule

    @model_validator(mode="after")
    def exact_units(self) -> Self:
        if set(self.units) != set(HOST_UNITS):
            message = "host unit projection must contain the four fixed units"
            raise ValueError(message)
        return self


class HostStatus(HostModel):
    schema_version: HostSchemaOne
    state: Literal["supported", "guarded", "unknown", "unavailable"]
    reason: HostReason | None
    profile: HostProfile | None
    binding: HostBinding | None
    permissions: HostPermissions
    permission_reasons: HostPermissionReasons
    facts: HostFacts | None

    @model_validator(mode="after")
    def coherent_authority(self) -> Self:
        known = self.state in {"supported", "guarded"}
        if (
            known != (self.reason is None)
            or known != (self.profile is not None)
            or known != (self.binding is not None)
            or known != (self.facts is not None)
        ):
            message = "host status state and authority disagree"
            raise ValueError(message)
        for name in HOST_ACTIONS:
            grant = getattr(self.permissions, name)
            reason = getattr(self.permission_reasons, name)
            if grant != (reason == "granted") or (not known and grant):
                message = "host status cannot grant unknown or contradictory authority"
                raise ValueError(message)
        if self.profile == "rootless" and (self.permissions.schedule or self.permissions.observer):
            message = "rootless schedule and observer are unproved"
            raise ValueError(message)
        if self.facts is not None and (
            (self.state == "guarded") != (self.facts.guard == "held")
            or (self.facts.guard == "held" and self.permissions.archive)
        ):
            message = "host guard evidence and archive permission disagree"
            raise ValueError(message)
        return self


def unavailable_host_status(reason: HostReason = "helper-unavailable") -> HostStatus:
    """Construct an explicit safe observation, without probing archive/helper paths."""
    reasons: dict[str, HostPermissionReason] = dict.fromkeys(HOST_ACTIONS, "helper-unavailable")
    return HostStatus(
        schema_version=1,
        state="unavailable",
        reason=reason,
        profile=None,
        binding=None,
        permissions=HostPermissions(**dict.fromkeys(HOST_ACTIONS, False)),
        permission_reasons=HostPermissionReasons(**reasons),
        facts=None,
    )
