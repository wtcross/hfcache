"""Durable journals, and the evidence that lets recovery trust them.

`docs/architecture.md` §7 is the contract. A journal at
`.store/transactions/<transaction-id>.json` opens **before** the first mutation
(`TX-01`) and records only what has already happened (`TX-02`) — never what a
process meant to do. That is the whole reason recovery can read one and act on
it: a dead process's intentions are worthless, but a durable record of a
completed rename is fact.

Three properties are implemented here rather than left to callers.

**Checkpoints are append-only and in the documented order.** Each operation has
a normative sequence of named checkpoints (§7.3-§7.7), and a journal whose names
are not a prefix of its operation's sequence is a combination no valid execution
produces — `HFTXN002`, which stops the machine (§7.9).

**Evidence is re-observable.** `TX-03` requires a checkpoint to carry facts that
can be checked against the filesystem, so recovery confirms rather than trusts.
The key naming convention that makes that mechanical is
`docs/progress.md` decision 42: a key ending `_path` names an archive-relative
path that must still exist, `_paths` a list of them, and `_absent` a path that
must *not* exist. Evidence that contradicts the filesystem is `HFTXN003`.

**Unknown keys survive a rewrite.** The journal is the only durable artifact
that is ever read, modified, and written back, which is why `docs/schemas.md`
§1.1's preservation rule applies to it alone (`docs/progress.md` decision 20).
A key this release does not know about is carried through untouched and reported,
never dropped.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, final

from hfcache.errors import Problem, SafetyError
from hfcache.identity import TransactionId
from hfcache.models import Checkpoint, TransactionError, TransactionJournal, dump, load
from hfcache.storage import atomic_write_bytes, fsync_directory

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from hfcache.identity import RunId
    from hfcache.paths import ArchiveLayout

__all__ = [
    "CHECKPOINTS",
    "JOURNAL_MODE",
    "PERMITTED_EXTRA_CHECKPOINTS",
    "JournalFile",
    "Transaction",
    "checkpoint_order_problems",
    "evidence_problems",
    "open_journals",
    "open_transaction",
    "read_journal",
]

JOURNAL_MODE: Final = 0o600
"""Journals live under `.store`, which is private to the writer (§5.2)."""

CHECKPOINTS: Final[Mapping[str, tuple[str, ...]]] = {
    # §7.3 — one per repository per newly observed SHA.
    "publication": (
        "staging_created",
        "download_completed",
        "content_hashed",
        "staging_built",
        "revision_tree_renamed",
        "manifest_published",
        "revision_ref_published",
        "current_ref_replaced",
        "catalog_rebuilt",
        "publication_committed",
    ),
    # §7.4 — checkpoint 7 is the commit point.
    "prune": (
        "plan_persisted",
        "cache_revision_deleted",
        "revision_ref_removed",
        "tree_tombstoned",
        "manifest_tombstoned",
        "catalog_published",
        "prune_logically_committed",
        "audit_record_written",
        "trash_removed",
        "prune_completed",
    ),
    # §7.5 — 4 and 8 are gates; 16-18 are the post-grace cleanup.
    "repair": (
        "evidence_preserved",
        "isolated_cache_created",
        "isolated_download_completed",
        "verified_against_original_manifest",
        "staging_built",
        "replacement_tree_renamed",
        "replacement_manifest_published",
        "replacement_reverified",
        "revision_ref_switched",
        "current_ref_switched",
        "catalog_rebuilt",
        "retirement_record_written",
        "implicated_cache_revision_deleted",
        "isolated_cache_removed",
        "repair_committed",
        "retired_tree_quarantined",
        "retired_manifest_archived",
        "repair_cleanup_completed",
    ),
    # §7.6 — one per invocation, correlating the per-repository journals.
    "sync": (
        "run_started",
        "preflight_passed",
        "journals_reconciled",
        "repositories_processed",
        "catalog_rebuilt",
        "run_report_written",
        "run_completed",
    ),
}
"""The normative checkpoint sequence for each operation (`docs/architecture.md` §7).

`recovery` is deliberately absent: §7.7 records one checkpoint per remediation,
so its sequence is as long as the work it found and cannot be enumerated here.
Its two closing checkpoints are still ordered, by `_RECOVERY_CLOSING`.
"""

PERMITTED_EXTRA_CHECKPOINTS: Final[Mapping[str, frozenset[str]]] = {
    # §7.4: a failure in steps 8-9 records this instead, after the commit point,
    # and only post-commit cleanup is retried later.
    "prune": frozenset({"cleanup_deferred"}),
}
"""Checkpoints a valid execution may record outside the documented sequence."""

_RECOVERY_CLOSING: Final = ("recovery_report_written", "recovery_completed")

_PATH_SUFFIX: Final = "_path"
_PATHS_SUFFIX: Final = "_paths"
_ABSENT_SUFFIX: Final = "_absent"


@final
@dataclass(frozen=True, slots=True)
class JournalFile:
    """A journal as it was read, including anything this release does not know.

    `unknown` is what `docs/schemas.md` §1.1 requires be preserved rather than
    dropped on rewrite. It is reported too — a journal carrying keys this build
    does not understand is worth an operator's attention even when the rewrite
    handles it correctly.
    """

    journal: TransactionJournal
    unknown: dict[str, Any] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        """Render for writing, with unknown keys merged back in."""
        if not self.unknown:
            return dump(self.journal)
        payload = json.loads(dump(self.journal)) | self.unknown
        return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )


def _now() -> datetime:
    return datetime.now(UTC)


@final
@dataclass(slots=True)
class Transaction:
    """An open journal, and the only way a checkpoint is ever appended.

    Mutable by design: a transaction is a live thing that accumulates
    checkpoints as its work becomes durable. Every append rewrites the whole
    journal atomically, because a partially appended journal would be exactly
    the ambiguity `TX-03` exists to prevent.
    """

    layout: ArchiveLayout
    file: JournalFile

    @property
    def journal(self) -> TransactionJournal:
        """The journal as it currently stands."""
        return self.file.journal

    @property
    def path(self) -> Path:
        """Where this journal lives."""
        return self.layout.journal(TransactionId(self.journal.transaction_id))

    def checkpoint(self, name: str, **evidence: Any) -> Checkpoint:  # noqa: ANN401 - evidence is arbitrary JSON by contract
        """Record that a named operation is durable (`TX-02`).

        Called *after* the act it names, never before. The name is checked
        against the operation's documented sequence, so a caller cannot record a
        checkpoint out of order and leave a journal no valid execution could
        have produced.
        """
        recorded = Checkpoint(
            evidence=evidence,
            name=name,
            recorded_at=_now(),
            sequence=len(self.journal.checkpoints) + 1,
        )
        updated = self.journal.model_copy(
            update={
                "checkpoints": (*self.journal.checkpoints, recorded),
                "last_checkpoint_at": recorded.recorded_at,
            }
        )
        if problems := checkpoint_order_problems(updated):
            raise SafetyError(problems)
        self._replace(updated)
        return recorded

    def commit(self) -> None:
        """Close the journal as `committed`: the work is done and durable."""
        self._close("committed")

    def fail(self, code: str, message: str) -> None:
        """Close the journal as `failed`, recording why in a redacted form."""
        self._close("failed", code=code, message=message)

    def needs_operator(self, code: str, message: str) -> None:
        """Stop and change nothing further (§7.9).

        Reached when recovery meets a state it may not resolve on its own. The
        journal stays as evidence and the archive stops accepting writes until
        an operator decides.
        """
        self._close("needs_operator", code=code, message=message)

    def _close(self, state: str, *, code: str | None = None, message: str | None = None) -> None:
        update: dict[str, Any] = {"completed_at": _now(), "state": state}
        if code is not None and message is not None:
            update["error"] = TransactionError(at=_now(), code=code, message=message)
        self._replace(self.journal.model_copy(update=update))

    def _replace(self, journal: TransactionJournal) -> None:
        """Revalidate and rewrite the whole journal, atomically."""
        # Round-tripped through the model rather than assigned, because
        # `model_copy` does not run validators and the journal's invariants —
        # sequence integrity, `last_checkpoint_at`, `completed_at` — are exactly
        # what a reader will rely on.
        validated = TransactionJournal.model_validate(journal.model_dump(mode="json"))
        self.file = JournalFile(journal=validated, unknown=self.file.unknown)
        _write(self.layout, self.file)


def _write(layout: ArchiveLayout, file: JournalFile) -> None:
    """Place a journal durably, and make its directory entry durable too."""
    path = layout.journal(TransactionId(file.journal.transaction_id))
    try:
        atomic_write_bytes(path, file.to_bytes(), mode=JOURNAL_MODE)
        fsync_directory(layout.transactions)
    except OSError as exc:
        message = f"the transaction journal {path} could not be written: {exc.strerror}"
        raise SafetyError.single(message, code="HFTXN001", location=str(path)) from exc


def open_transaction(  # noqa: PLR0913 - the journal's required identity fields, one each
    layout: ArchiveLayout,
    *,
    transaction_id: TransactionId,
    operation: str,
    run_id: RunId,
    archive_id: str,
    config_fingerprint: str,
    **scope: Any,  # noqa: ANN401 - the optional narrowing fields, as JSON
) -> Transaction:
    """Open a journal before the first mutation (`TX-01`).

    Durable before this returns, so a crash between opening and the first act
    still leaves a journal naming the transaction — which is what makes the
    staging directory it is about to create recognisable rather than orphaned
    (§7.8).

    `scope` carries the optional narrowing fields a publication, prune, or
    repair sets: `repository_id`, `repository_type`, `commit_sha`,
    `publication_id`.
    """
    journal = TransactionJournal.model_validate(
        {
            "archive_id": archive_id,
            "config_fingerprint": config_fingerprint,
            "created_at": _now(),
            "operation": operation,
            "run_id": run_id,
            "state": "open",
            "transaction_id": transaction_id,
            **scope,
        }
    )
    file = JournalFile(journal=journal)
    _write(layout, file)
    return Transaction(layout=layout, file=file)


def read_journal(layout: ArchiveLayout, path: Path) -> JournalFile:
    """Read one journal, preserving anything this release does not understand.

    `HFTXN001` for a file that will not load or whose `schema_version` is newer
    than this build's — §7.9's first stopping condition, and the reason recovery
    never acts on a journal it cannot fully read.
    """
    where = str(layout.archive_relative(path))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        message = f"the transaction journal {path} could not be read: {exc.strerror}"
        raise SafetyError.single(message, code="HFTXN001", location=where) from exc
    try:
        payload = json.loads(raw)
    except ValueError as exc:
        message = f"the transaction journal {path} is not valid JSON: {exc}"
        raise SafetyError.single(message, code="HFTXN001", location=where) from exc
    if not isinstance(payload, dict):
        message = f"the transaction journal {path} is not a JSON object"
        raise SafetyError.single(message, code="HFTXN001", location=where)

    known = {key: value for key, value in payload.items() if key in TransactionJournal.model_fields}
    unknown = {key: value for key, value in payload.items() if key not in known}
    journal = load(
        TransactionJournal,
        json.dumps(known),
        error=SafetyError,
        code="HFTXN001",
        location=where,
    )
    return JournalFile(journal=journal, unknown=unknown)


def open_journals(layout: ArchiveLayout) -> tuple[JournalFile, ...]:
    """Every journal a mutating command must reconcile before it acts (`TX-07`).

    Resolved journals — `committed` or `failed` — are left alone: they describe
    work that reached a conclusion, and reconciliation has nothing to do with
    them. A `needs_operator` journal is *not* resolved and is returned, because
    it is precisely what must stop the next run.
    """
    try:
        entries = sorted(layout.transactions.iterdir())
    except OSError:
        return ()
    files = [read_journal(layout, entry) for entry in entries if entry.suffix == ".json"]
    return tuple(file for file in files if not file.journal.is_resolved)


def checkpoint_order_problems(journal: TransactionJournal) -> list[Problem]:
    """Report a checkpoint sequence no valid execution produces (`HFTXN002`).

    The model already guarantees the *numbers* start at 1 and increase by one.
    This checks the *names* against the operation's documented sequence, which
    is what catches a journal assembled by hand, corrupted in a way that still
    parses, or written by a build whose ordering differed.
    """
    names = [checkpoint.name for checkpoint in journal.checkpoints]
    if journal.operation == "recovery":
        return _recovery_order_problems(journal, names)

    expected = CHECKPOINTS[journal.operation]
    permitted = PERMITTED_EXTRA_CHECKPOINTS.get(journal.operation, frozenset())
    core = [name for name in names if name not in permitted]
    if core == list(expected[: len(core)]):
        return []
    message = (
        f"{journal.operation} journal {journal.transaction_id} records checkpoints {names}, "
        f"which is not a prefix of the documented sequence {list(expected)}; no valid "
        f"execution produces this combination"
    )
    return [
        Problem(
            code="HFTXN002",
            message=message,
            location=str(journal.transaction_id),
            context={"expected": list(expected), "recorded": names},
        )
    ]


def _recovery_order_problems(journal: TransactionJournal, names: list[str]) -> list[Problem]:
    """A recovery journal records one checkpoint per remediation, then closes.

    Its length is whatever it found, so only the two closing checkpoints are
    ordered: they come last, in sequence, and nothing follows them.
    """
    closing = [name for name in names if name in _RECOVERY_CLOSING]
    tail = names[len(names) - len(closing) :] if closing else []
    if closing == tail == list(_RECOVERY_CLOSING[: len(closing)]):
        return []
    message = (
        f"recovery journal {journal.transaction_id} records {names}; its closing checkpoints "
        f"must be {list(_RECOVERY_CLOSING)}, in that order, with nothing after them"
    )
    return [Problem(code="HFTXN002", message=message, location=str(journal.transaction_id))]


def evidence_problems(layout: ArchiveLayout, journal: TransactionJournal) -> list[Problem]:
    """Confirm every checkpoint's evidence against the filesystem (`TX-03`).

    A checkpoint says an operation was durable; this asks whether that is still
    true. Disagreement is `HFTXN003` and stops the machine (§7.9), because a
    journal that contradicts the archive cannot be used to decide anything about
    it.

    Only path evidence is mechanically checkable, which is what the key naming
    convention is for (decision 42). Counts and digests are checked by the
    packages that know how to interpret them.
    """
    problems: list[Problem] = []
    for checkpoint in journal.checkpoints:
        for key, value in sorted(checkpoint.evidence.items()):
            problems.extend(_entry_problems(layout, checkpoint, key, value))
    return problems


def _entry_problems(
    layout: ArchiveLayout, checkpoint: Checkpoint, key: str, value: object
) -> list[Problem]:
    """Check one evidence entry, if its key says it names a path."""
    if key.endswith(_PATHS_SUFFIX) and isinstance(value, list):
        return [
            problem
            for item in value
            for problem in _path_problems(layout, checkpoint, key, item, present=True)
        ]
    if key.endswith(_PATH_SUFFIX) and isinstance(value, str):
        return _path_problems(layout, checkpoint, key, value, present=True)
    if key.endswith(_ABSENT_SUFFIX) and isinstance(value, str):
        return _path_problems(layout, checkpoint, key, value, present=False)
    return []


def _path_problems(
    layout: ArchiveLayout, checkpoint: Checkpoint, key: str, value: object, *, present: bool
) -> list[Problem]:
    """One archive-relative path, and whether the filesystem agrees about it."""
    try:
        target = layout.resolve(value, code="HFTXN003")
    except ValueError as exc:
        return [
            Problem(
                code="HFTXN003",
                message=f"checkpoint {checkpoint.name} evidence {key} is unusable: {exc}",
                location=f"{checkpoint.name}.{key}",
            )
        ]
    if target.exists() == present:
        return []
    state = "does not exist" if present else "still exists"
    message = (
        f"checkpoint {checkpoint.name} recorded {key}={value}, but {target} {state}; the "
        f"journal and the archive disagree about what happened"
    )
    return [Problem(code="HFTXN003", message=message, location=f"{checkpoint.name}.{key}")]
