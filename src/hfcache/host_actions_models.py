"""Closed fixed host-action projections; INV022/ADR156 and schemas18.7."""

import re
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from hfcache.host_models import (  # noqa: TC001 - Pydantic runtime field authorities
    HostBinding,
    HostPermissionReason,
    HostProfile,
    HostReason,
    HostSchemaOne,
)
from hfcache.logging import EVENTS
from hfcache.models import ArchiveIdField, RunIdField, Sha256, Timestamp, as_tuple

MAXIMUM_CALENDAR_CHARS = 4096
MAXIMUM_DELAY_CHARS = 256
MAXIMUM_CURSOR_CHARS = 2048
MAXIMUM_JOURNAL_ENTRIES = 80
MAXIMUM_JOURNAL_ENTRY_BYTES = 8192
MAXIMUM_JOURNAL_TEXT_BYTES = 65536
MAXIMUM_JOURNAL_PAGE_BYTES = 524288
JOURNAL_SOURCES = ("sync-observer", "verify-observer")
JOURNAL_EVENTS = frozenset(EVENTS)
_OUTCOME_STATES = Literal[
    "prepared", "unchanged", "effect_unconfirmed", "confirmed", "conflict", "unknown"
]


def _printable(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[\x20-\x7e]+", value) is None:
        message = "host value must be bounded printable ASCII"
        raise ValueError(message)
    return value


def _schedule_text(value: object) -> str:
    result = _printable(value)
    if not result.strip() or "\\" in result:
        message = "schedule value must be one nonempty safe line"
        raise ValueError(message)
    return result


def _journal_message(value: object) -> str:
    result = _printable(value)
    match = re.fullmatch(
        r"event=([a-z][a-z0-9_.-]{0,63}) level=(debug|info|warning|error|critical) "
        r"run_id=([0-9a-f]{32})",
        result,
    )
    if match is None or match[1] not in JOURNAL_EVENTS:
        message = "journal entry must contain only a recognized diagnostic projection"
        raise ValueError(message)
    return result


Calendar = Annotated[
    str, BeforeValidator(_schedule_text), Field(min_length=1, max_length=MAXIMUM_CALENDAR_CHARS)
]
Delay = Annotated[
    str, BeforeValidator(_schedule_text), Field(min_length=1, max_length=MAXIMUM_DELAY_CHARS)
]
Cursor = Annotated[
    str, BeforeValidator(_printable), Field(min_length=1, max_length=MAXIMUM_CURSOR_CHARS)
]
Description = Annotated[str, BeforeValidator(_printable), Field(min_length=1, max_length=512)]
JournalSource = Literal["sync-observer", "verify-observer"]
ScheduleAction = Literal["pause", "resume", "replace", "reset"]


class HostActionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class HostActionRequest(HostActionModel):
    def canonical_body(self) -> dict[str, Any]:
        """Preserve required nulls while omitting the union's absent fields."""
        return self.model_dump(mode="json", exclude_unset=True)


class ScheduleValidationRequest(HostActionRequest):
    on_calendar: Calendar
    randomized_delay_sec: Delay | None


class ScheduleValidation(HostActionModel):
    schema_version: HostSchemaOne
    archive_id: ArchiveIdField
    on_calendar: Calendar
    randomized_delay_sec: Delay | None
    normalized_on_calendar: Calendar
    normalized_randomized_delay_sec: Delay | None
    next_elapse: Description | None

    @model_validator(mode="after")
    def coherent_delay(self) -> Self:
        if (self.randomized_delay_sec is None) != (self.normalized_randomized_delay_sec is None):
            message = "validated delay and requested delay disagree"
            raise ValueError(message)
        return self


class ScheduleChangeRequest(HostActionRequest):
    action: ScheduleAction
    expected_revision: Sha256
    on_calendar: Calendar | None = None
    randomized_delay_sec: Delay | None = None

    @model_validator(mode="after")
    def exact_action(self) -> Self:
        fields = {"action", "expected_revision"}
        if self.action == "replace":
            fields |= {"on_calendar", "randomized_delay_sec"}
        if self.model_fields_set != fields or (
            self.action == "replace" and self.on_calendar is None
        ):
            message = "schedule action fields do not match their fixed variant"
            raise ValueError(message)
        return self


class ObserverExpected(HostActionModel):
    boot_id: ArchiveIdField
    invocation_id: RunIdField
    main_pid: Annotated[int, Field(ge=2, le=2147483647)]
    start_ticks: Annotated[int, Field(ge=1, le=9007199254740991)]


class ObserverStopRequest(HostActionRequest):
    expected: ObserverExpected


class HostActionPermissions(HostActionModel):
    schedule: bool
    observer: bool


class HostActionPermissionReasons(HostActionModel):
    schedule: HostPermissionReason
    observer: HostPermissionReason


class HostObserverStatus(HostActionModel):
    schema_version: HostSchemaOne
    archive_id: ArchiveIdField
    profile: HostProfile | None
    host_binding: HostBinding | None
    permissions: HostActionPermissions
    permission_reasons: HostActionPermissionReasons
    state: Literal["observed", "inactive", "unavailable"]
    reason: HostReason | Literal["profile-unproved"] | None
    unit: Literal["hfcache-sync.service"]
    expected: ObserverExpected | None

    @model_validator(mode="after")
    def coherent_authority(self) -> Self:
        if (self.profile is None) != (self.host_binding is None) or (
            self.host_binding is not None and self.host_binding.archive_id != self.archive_id
        ):
            message = "observer host binding and archive disagree"
            raise ValueError(message)
        known = self.state in {"observed", "inactive"}
        if known:
            if (
                self.profile != "native"
                or self.host_binding is None
                or self.reason is not None
                or (self.expected is not None) != (self.state == "observed")
            ):
                message = "observer state and original invocation disagree"
                raise ValueError(message)
        elif self.reason is None or self.expected is not None:
            message = "unavailable observer cannot carry an invocation"
            raise ValueError(message)
        for name in ("schedule", "observer"):
            granted = getattr(self.permissions, name)
            reason = getattr(self.permission_reasons, name)
            if granted != (reason == "granted") or (not known and granted):
                message = "observer permissions cannot grant unknown authority"
                raise ValueError(message)
        if self.profile == "rootless" and (
            self.state != "unavailable"
            or self.reason != "profile-unproved"
            or any(
                getattr(self.permission_reasons, name) != "profile-unproved"
                for name in ("schedule", "observer")
            )
        ):
            message = "rootless host actions remain profile-unproved"
            raise ValueError(message)
        return self


class HostActionOutcome(HostActionModel):
    schema_version: HostSchemaOne
    archive_id: ArchiveIdField
    operation_id: RunIdField
    request_digest: Sha256
    state: _OUTCOME_STATES
    pending: bool


class ScheduleChangeOutcome(HostActionOutcome):
    action: ScheduleAction | None
    expected_revision: Sha256 | None
    stored_revision: Sha256 | None
    file_state: Literal["unchanged", "installed", "removed", "unknown"]
    manager_state: Literal["not_sent", "reload_acknowledged", "timer_acknowledged", "unknown"]
    timer_was_active: bool | None
    timer_is_active: bool | None

    @model_validator(mode="after")
    def coherent_effect(self) -> Self:
        if self.state != "unknown" and any(
            value is None for value in (self.action, self.expected_revision, self.stored_revision)
        ):
            message = "known schedule outcome requires its original revisions"
            raise ValueError(message)
        if (self.action is None) != (self.expected_revision is None) or (
            self.action is None
            and any(
                value is not None
                for value in (self.stored_revision, self.timer_was_active, self.timer_is_active)
            )
        ):
            message = "schedule outcome original identity is incomplete"
            raise ValueError(message)
        if self.state in {"prepared", "unchanged"} and (
            self.file_state != "unchanged"
            or self.manager_state != "not_sent"
            or (
                self.state == "prepared"
                and (not self.pending or self.expected_revision != self.stored_revision)
            )
            or (
                self.state == "unchanged"
                and (
                    self.pending
                    or self.timer_was_active is None
                    or self.timer_is_active != self.timer_was_active
                )
            )
        ):
            message = "no-effect schedule state contradicts its evidence"
            raise ValueError(message)
        if self.state == "confirmed":
            valid = self.timer_was_active is not None and self.timer_is_active is not None
            if self.action in {"pause", "resume"}:
                valid = (
                    valid
                    and self.file_state == "unchanged"
                    and self.expected_revision == self.stored_revision
                    and self.manager_state == "timer_acknowledged"
                    and self.timer_is_active == (self.action == "resume")
                )
            else:
                valid = (
                    valid
                    and self.file_state
                    in ({"installed"} if self.action == "replace" else {"removed", "unchanged"})
                    and self.timer_is_active == self.timer_was_active
                    and self.manager_state
                    == ("timer_acknowledged" if self.timer_was_active else "reload_acknowledged")
                )
            if not valid:
                message = "confirmed schedule outcome lacks exact file and manager evidence"
                raise ValueError(message)
        return self


class ObserverStopOutcome(HostActionOutcome):
    expected: ObserverExpected | None
    stop_state: Literal["not_sent", "acknowledged", "exit_confirmed", "unknown"]

    @model_validator(mode="after")
    def coherent_effect(self) -> Self:
        if (self.state != "unknown" and self.expected is None) or (
            self.state == "confirmed" and self.stop_state != "exit_confirmed"
        ):
            message = "observer outcome lacks original exit evidence"
            raise ValueError(message)
        if self.state in {"prepared", "unchanged"} and (
            self.stop_state != "not_sent" or (self.state == "prepared" and not self.pending)
        ):
            message = "no-effect observer state contradicts its evidence"
            raise ValueError(message)
        return self


class JournalQuery(HostActionModel):
    source: JournalSource
    cursor: Cursor | None = None
    limit: Annotated[int, Field(ge=1, le=MAXIMUM_JOURNAL_ENTRIES)] = MAXIMUM_JOURNAL_ENTRIES


class HostJournalEntry(HostActionModel):
    at: Timestamp | None
    message: Annotated[
        str, BeforeValidator(_journal_message), Field(max_length=MAXIMUM_JOURNAL_ENTRY_BYTES)
    ]


class HostJournalPage(HostActionModel):
    schema_version: HostSchemaOne
    archive_id: ArchiveIdField
    source: JournalSource
    entries: Annotated[
        tuple[HostJournalEntry, ...],
        BeforeValidator(as_tuple),
        Field(max_length=MAXIMUM_JOURNAL_ENTRIES),
    ]
    next_cursor: Cursor | None
    gap: bool
    truncated: bool

    @model_validator(mode="after")
    def bounded_page(self) -> Self:
        if (
            sum(len(row.message.encode("utf-8")) for row in self.entries)
            > MAXIMUM_JOURNAL_TEXT_BYTES
        ):
            message = "journal diagnostic text exceeds its display budget"
            raise ValueError(message)
        if len(self.model_dump_json().encode("utf-8")) > MAXIMUM_JOURNAL_PAGE_BYTES:
            message = "journal page exceeds its encoded budget"
            raise ValueError(message)
        return self
