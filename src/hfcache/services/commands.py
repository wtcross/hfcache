"""Typed application commands with explicit common-lock ownership (decision 110).

Domain modules retain archive algorithms and durable formats; adapters only parse
and render. No transport framework is imported here (INV-012).
"""

import socket
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final

from hfcache.archive import initialize_archive
from hfcache.credentials import resolve_token
from hfcache.errors import (
    ConfigurationError,
    ExitCode,
    HfcacheError,
    IntegrityError,
    Problem,
    SafetyError,
)
from hfcache.hub import HubClient
from hfcache.identity import (
    RepositoryIdentity,
    RunId,
    TransactionId,
    new_transaction_id,
    parse_selector,
)
from hfcache.locking import exclusive_lock, lock_path
from hfcache.logging import emit, under_systemd
from hfcache.paths import ArchiveLayout
from hfcache.preflight import (
    READ_ONLY,
    UNPROVABLE_READ_ONLY,
    Check,
    guarded,
    hub_checks,
    order_checks,
    storage_checks,
)
from hfcache.publication import projected_publication_bytes, published_repositories
from hfcache.purge import apply_purge, plan_all_purges
from hfcache.quarantine import apply_quarantine_cleanup, plan_quarantine_cleanups
from hfcache.recovery import apply_recovery, plan_recovery, reconcile
from hfcache.redaction import redact_text
from hfcache.repair import repair_revision
from hfcache.reporting import RecoveryReport, RunReport, RuntimeVersions
from hfcache.retention import apply_prune, plan_all
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.services.queries import LocalQueries
from hfcache.services.requests import (
    ALL_CONFIGURED,
    DoctorRequest,
    InitializationRequest,
    MaintenanceRequest,
    QuarantineRequest,
    RepairRequest,
    SelectionRequest,
    VerificationRequest,
    _chosen_modes,
    _mode_option,
    _verification_mode,
)
from hfcache.storage import read_model
from hfcache.sync import synchronize
from hfcache.transactions import open_transaction
from hfcache.verification import (
    FINDING_CODES,
    build_report,
    persist_verification,
    require_retained,
    resolve_archive,
    resolve_run,
    verify_targets,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from hfcache.config import ApplicationConfig, RepositoryConfig
    from hfcache.models import PrunePlan
    from hfcache.reporting import VerificationReport
    from hfcache.sync import RunOutcome
    from hfcache.verification import Resolved


# Existing server adapters retain these compatibility exports (decision 120).
__all__ = [
    "ALL_CONFIGURED",
    "CommandServices",
    "DoctorRequest",
    "InitializationRequest",
    "MaintenanceRequest",
    "QuarantineRequest",
    "RepairRequest",
    "SelectionRequest",
    "VerificationRequest",
    "_chosen_modes",
    "_mode_option",
    "_verification_mode",
]


def _failure(
    command: str, error: HfcacheError, payload: dict[str, Any] | None = None
) -> ServiceResult:
    return ServiceResult(
        command, payload or {}, errors=error.problems, exit_code=int(error.exit_code)
    )


@dataclass(frozen=True, slots=True)
class CommandServices:
    """One frozen policy/execution snapshot; public commands acquire their own lock.

    Domain functions called inside these methods never acquire a second service
    lock. Every non-estimate verification holds its storage safety proof through
    report/catalog persistence (INV-007, decision 110).
    """

    config: ApplicationConfig
    context: ExecutionContext
    token_file: Path | None = None
    config_label: str = "installed configuration"

    @property
    def layout(self) -> ArchiveLayout:
        """The configured archive, never a caller-selected filesystem path."""
        return ArchiveLayout(root=self.config.storage.archive_root)

    def initialize_archive(self, request: InitializationRequest) -> ServiceResult:
        """Inspect and initialize under the common lock, without requiring a sentinel."""
        with self.context.activate():
            command = "archive init"
            payload: dict[str, Any] = {}
            try:
                _check_init_options(
                    self.config,
                    archive_root=request.archive_root,
                    archive_id=request.archive_id,
                    confirm=request.confirm,
                    inspect=request.inspect,
                )
                # Inspection/no-confirm remain read-only. Explicit creation owns the
                # lock before its fresh inspection; sentinel preflight cannot run
                # before the command whose purpose is to create that sentinel.
                lock = (
                    exclusive_lock(
                        lock_path(),
                        command=command,
                        wait_seconds=self.config.sync.lock_wait_seconds,
                    )
                    if request.confirm
                    else nullcontext()
                )
                with lock:
                    inspection = LocalQueries(self.config).inspect_archive()
                    payload = inspection.as_payload()
                    if inspection.problems:
                        raise SafetyError(inspection.problems)
                    if request.inspect:
                        return ServiceResult(command, payload)
                    if not inspection.initializable:
                        message = (
                            f"archive {self.layout.root} is already initialized; "
                            "initialization happens once, because a second sentinel would give an "
                            "existing archive a new identity"
                        )
                        raise SafetyError.single(
                            message, code="HFMNT014", location=str(self.layout.root)
                        )
                    if not request.confirm:
                        message = (
                            f"--confirm is required to initialize {self.layout.root}; "
                            "nothing was changed. "
                            "The reported state is what initialization would act on"
                        )
                        raise ConfigurationError.single(
                            message, code="HFARG003", location=str(self.layout.root)
                        )
                    initialized = initialize_archive(
                        self.layout, archive_id=self.config.storage.archive_id
                    )
                    return ServiceResult(command, initialized.as_payload())
            except HfcacheError as error:
                return _failure(command, error, payload)

    def diagnose(self, request: DoctorRequest) -> ServiceResult:
        """Run every diagnostic check; probe writes hold the shared lock."""
        with self.context.activate():
            command = "doctor"
            try:
                token = resolve_token(self.config.hub, token_file=self.token_file)
                lock = (
                    nullcontext()
                    if request.read_only
                    else exclusive_lock(
                        lock_path(),
                        command=command,
                        wait_seconds=self.config.sync.lock_wait_seconds,
                    )
                )
                with lock:
                    checks = [
                        Check.passed(
                            "configuration",
                            f"{self.config_label} is valid; "
                            f"fingerprint {self.config.fingerprint()[:12]}",
                        ),
                        *storage_checks(
                            self.layout, storage=self.config.storage, read_only=request.read_only
                        ),
                        Check.passed("credential", token.describe()),
                        Check.passed(
                            "hub_endpoint",
                            f"{self.config.hub.endpoint} is a well-formed https endpoint",
                        ),
                        *hub_checks(
                            self.config.hub, HubClient.of(token, endpoint=self.config.hub.endpoint)
                        ),
                    ]
                    if request.read_only:
                        probed = {check.name for check in checks}
                        checks.extend(
                            Check.skipped(name, READ_ONLY)
                            for name in UNPROVABLE_READ_ONLY
                            if name not in probed
                        )
                    ordered = order_checks(checks)
                    problems = tuple(problem for check in ordered for problem in check.problems)
                    warnings = tuple(warning for check in ordered for warning in check.warnings)
                    failed = any(check.outcome == "fail" for check in ordered)
                    return ServiceResult(
                        command,
                        {"checks": [check.as_entry() for check in ordered]},
                        warnings=warnings,
                        errors=problems,
                        exit_code=int(ExitCode.SAFETY) if failed else 0,
                    )
            except HfcacheError as error:
                return _failure(command, error)

    def plan_sync(self, request: SelectionRequest = ALL_CONFIGURED) -> ServiceResult:
        """Resolve and cost configured repositories without locks or archive writes."""
        with self.context.activate():
            try:
                token = resolve_token(self.config.hub, token_file=self.token_file)
                selected = _select(self.config, list(request.selectors))
                client = HubClient.of(token, endpoint=self.config.hub.endpoint)
                client.require_identity(self.config.hub.expected_account)
                entries: list[dict[str, Any]] = []
                problems: list[Problem] = []
                for repository in selected:
                    if repository.enabled:
                        entry, failure = _planned(
                            client, repository, self.config, cache_dir=self.layout.hub_cache
                        )
                        entries.append(entry)
                        if failure is not None:
                            problems.append(failure)
                return ServiceResult(
                    "plan",
                    {"repositories": entries},
                    errors=tuple(problems),
                    exit_code=int(ExitCode.SYNC) if problems else 0,
                )
            except HfcacheError as error:
                return _failure("plan", error)

    def synchronize(self, request: SelectionRequest = ALL_CONFIGURED) -> ServiceResult:
        """Guard, reconcile, then run the existing bounded/joined transfer engine."""
        with self.context.activate():
            try:
                token = resolve_token(self.config.hub, token_file=self.token_file)
                selected = _select(self.config, list(request.selectors))
                client = HubClient.of(token, endpoint=self.config.hub.endpoint)
                envelope = _run_envelope(self.config)
                with guarded(
                    self.layout,
                    storage=self.config.storage,
                    command="sync",
                    lock_wait_seconds=self.config.sync.lock_wait_seconds,
                ) as checks:
                    emit(
                        "run.started",
                        command="sync",
                        archive_id=str(envelope["archive_id"]),
                        config_fingerprint=str(envelope["config_fingerprint"]),
                        repositories=len(selected),
                        invocation=str(envelope["invocation_mode"]),
                    )
                    outcome = _run(
                        client,
                        self.layout,
                        self.config,
                        selected=selected,
                        envelope=envelope,
                        checks=checks,
                        run_id=self.context.run_id,
                        started_at=self.context.started_at,
                    )
                payload = outcome.report.model_dump(mode="json")
                payload["report"] = str(self.layout.archive_relative(outcome.report_path))
                problems = tuple(
                    Problem(
                        code=code,
                        message=f"{item.repository_type}:{item.repository_id} failed",
                        repository=f"{item.repository_type}:{item.repository_id}",
                    )
                    for item in outcome.report.repositories
                    for code in item.errors
                )
                warnings = tuple(
                    Problem(
                        code=code,
                        message=f"{item.repository_type}:{item.repository_id} warned",
                        repository=f"{item.repository_type}:{item.repository_id}",
                    )
                    for item in outcome.report.repositories
                    for code in item.warnings
                )
                return ServiceResult(
                    "sync",
                    payload,
                    warnings,
                    problems,
                    int(outcome.exit_code),
                    run_id=self.context.run_id,
                )
            except HfcacheError as error:
                return _failure("sync", error)

    def verify(self, request: VerificationRequest) -> ServiceResult:
        """Resolve, hash, write report, and merge catalog within one archive lock."""
        with self.context.activate():
            command = request.command
            payload: dict[str, Any] = {}
            try:
                mode = request.mode
                if mode == "estimate":
                    return LocalQueries(self.config).estimate_verification()
                guard = guarded(
                    self.layout,
                    storage=self.config.storage,
                    command=command,
                    lock_wait_seconds=self.config.verification.lock_wait_seconds,
                )
                with guard:
                    if mode == "full":
                        targets = resolve_archive(self.layout)
                    elif mode == "revision":
                        targets = (_named_revision(self.layout, str(request.revision)),)
                    else:
                        targets = resolve_run(
                            self.layout, _run_to_verify(self.layout, request.run_id)
                        )
                    outcome = verify_targets(targets, started_at=self.context.started_at)
                    report = build_report(
                        outcome,
                        envelope=_run_envelope(self.config),
                        command=command,
                        mode=mode,
                        run_id=self.context.run_id,
                    )
                    payload = report.model_dump(mode="json")
                    report_path = persist_verification(self.layout, report, outcome, mode=mode)
                    payload["report"] = str(self.layout.archive_relative(report_path))
                    emit(
                        "verification.completed",
                        command=command,
                        outcome=report.verification_outcome,
                        exit_code=report.exit_code,
                        repositories=report.scope.repositories,
                        revisions=report.scope.revisions,
                        objects_read=report.scope.unique_objects_read,
                        bytes_read=report.scope.unique_bytes_read,
                        findings=len(report.findings),
                        report=payload["report"],
                    )
                    return ServiceResult(
                        command,
                        payload,
                        errors=tuple(_finding_problems(report)),
                        exit_code=report.exit_code,
                        run_id=RunId(report.run_id),
                    )
            except HfcacheError as error:
                return _failure(command, error, payload)

    def prune(self, request: MaintenanceRequest) -> ServiceResult:
        """Plan under ownership on apply, preserving reconciliation-before-work."""
        with self.context.activate():
            command = f"prune {'--apply' if request.apply else '--dry-run'}"
            try:
                request.require_mode()
                wanted = {
                    RepositoryIdentity.from_config(repository).selector
                    for repository in _select(self.config, list(request.selectors))
                }
                if request.apply:
                    with guarded(
                        self.layout,
                        storage=self.config.storage,
                        command=command,
                        lock_wait_seconds=self.config.sync.lock_wait_seconds,
                    ):
                        envelope = _run_envelope(self.config) | {"run_id": self.context.run_id}
                        self._reconcile(envelope)
                        plans = _plans(
                            self.layout, wanted, maximum=self.config.storage.maximum_revisions
                        )
                        applied = [
                            apply_prune(self.layout, plan, envelope=envelope) for plan in plans
                        ]
                else:
                    plans = _plans(
                        self.layout, wanted, maximum=self.config.storage.maximum_revisions
                    )
                    applied = []
                return ServiceResult(
                    command,
                    {
                        "plans": [plan.model_dump(mode="json") for plan in plans],
                        "applied": [record.model_dump(mode="json") for record in applied],
                    },
                )
            except HfcacheError as error:
                return _failure(command, error)

    def purge(self, request: MaintenanceRequest) -> ServiceResult:
        """Re-resolve explicit unmanaged scope under the apply lock after recovery."""
        with self.context.activate():
            command = f"purge {'--apply' if request.apply else '--dry-run'}"
            try:
                request.require_mode()
                identities = _purge_identities(
                    self.config,
                    self.layout,
                    list(request.selectors),
                    all_unmanaged=request.all_unmanaged,
                )
                if request.apply:
                    with guarded(
                        self.layout,
                        storage=self.config.storage,
                        command=command,
                        lock_wait_seconds=self.config.sync.lock_wait_seconds,
                    ):
                        envelope = _run_envelope(self.config) | {"run_id": self.context.run_id}
                        self._reconcile(envelope)
                        identities = _purge_identities(
                            self.config,
                            self.layout,
                            list(request.selectors),
                            all_unmanaged=request.all_unmanaged,
                        )
                        plans = plan_all_purges(
                            self.layout, identities, generated_at=datetime.now(UTC)
                        )
                        applied = [
                            record.model_dump(mode="json")
                            for plan in plans
                            for record in apply_purge(self.layout, plan, envelope=envelope)
                        ]
                else:
                    plans = plan_all_purges(self.layout, identities, generated_at=datetime.now(UTC))
                    applied = []
                return ServiceResult(
                    command,
                    {"plans": [plan.model_dump(mode="json") for plan in plans], "applied": applied},
                )
            except HfcacheError as error:
                return _failure(command, error)

    def recover(self, request: MaintenanceRequest) -> ServiceResult:
        """Report blocked plans alongside refusals; never reconcile implicitly."""
        with self.context.activate():
            command = f"recover {'--apply' if request.apply else '--dry-run'}"
            payload: dict[str, Any] = {}
            report_id: RunId | None = None
            try:
                request.require_mode()
                guard = (
                    guarded(
                        self.layout,
                        storage=self.config.storage,
                        command=command,
                        lock_wait_seconds=self.config.sync.lock_wait_seconds,
                    )
                    if request.apply
                    else nullcontext()
                )
                with guard:
                    plan = plan_recovery(
                        self.layout,
                        stale_staging_age_hours=self.config.sync.stale_staging_age_hours,
                    )
                    payload = plan.as_payload()
                    if not plan.blocked and request.apply:
                        report_path, applied = apply_recovery(
                            self.layout,
                            plan,
                            envelope=_run_envelope(self.config),
                            started_at=self.context.started_at,
                            run_id=self.context.run_id,
                        )
                        payload |= {
                            "applied": len(applied),
                            "report": str(self.layout.archive_relative(report_path)),
                        }
                        report_id = RunId(
                            read_model(
                                report_path, RecoveryReport, error=IntegrityError, code="HFVER007"
                            ).run_id
                        )
                if plan.blocked:
                    raise SafetyError(list(plan.problems))
                return ServiceResult(command, payload, run_id=report_id)
            except HfcacheError as error:
                return _failure(command, error, payload)

    def quarantine(self, request: QuarantineRequest) -> ServiceResult:
        """Refuse unfinished unrelated work; never run reconciliation for cleanup."""
        with self.context.activate():
            command = f"quarantine {'--apply' if request.apply else '--dry-run'}"
            try:
                if request.dry_run == request.apply:
                    message = "exactly one of --dry-run and --apply is required"
                    raise ConfigurationError.single(message, code="HFARG002")
                if not request.transaction_ids:
                    message = "quarantine cleanup requires explicit transaction ids"
                    raise ConfigurationError.single(message, code="HFARG003")
                identifiers = tuple(
                    TransactionId(value) for value in sorted(set(request.transaction_ids))
                )
                for identifier in identifiers:
                    try:
                        self.layout.quarantine_for(identifier)
                    except ValueError as exc:
                        raise ConfigurationError.single(
                            str(exc), code="HFARG001", location=str(identifier)
                        ) from exc
                guard = (
                    guarded(
                        self.layout,
                        storage=self.config.storage,
                        command=command,
                        lock_wait_seconds=self.config.sync.lock_wait_seconds,
                    )
                    if request.apply
                    else nullcontext()
                )
                with guard:
                    plans = plan_quarantine_cleanups(self.layout, identifiers)
                    applied = (
                        [apply_quarantine_cleanup(self.layout, plan) for plan in plans]
                        if request.apply
                        else []
                    )
                return ServiceResult(
                    command, {"plans": [plan.to_dict() for plan in plans], "applied": applied}
                )
            except HfcacheError as error:
                return _failure(command, error)

    def repair(self, request: RepairRequest) -> ServiceResult:
        """Repair one immutable SHA against its original expectations (AD-13)."""
        with self.context.activate():
            try:
                parsed = request.target
                token = resolve_token(self.config.hub, token_file=self.token_file)
                client = HubClient.of(token, endpoint=self.config.hub.endpoint)
                envelope = _run_envelope(self.config)
                with guarded(
                    self.layout,
                    storage=self.config.storage,
                    command="repair",
                    lock_wait_seconds=self.config.sync.lock_wait_seconds,
                ):
                    self._reconcile(envelope)
                    client.require_identity(self.config.hub.expected_account)
                    outcome = repair_revision(
                        client,
                        self.layout,
                        self.config,
                        identity=parsed.identity,
                        commit_sha=request.commit_sha,
                        # Credentials are registered by resolve_token above; audit
                        # must not preserve a known bearer or Hub secret (INV-002).
                        reason=redact_text(request.reason),
                        envelope=envelope,
                        run_id=self.context.run_id,
                    )
                return ServiceResult("repair", outcome.as_payload(), run_id=self.context.run_id)
            except HfcacheError as error:
                return _failure("repair", error)

    def _reconcile(self, envelope: Mapping[str, Any]) -> None:
        """Private helper requiring the caller's existing common-lock ownership."""
        reconcile(
            self.layout,
            stale_staging_age_hours=self.config.sync.stale_staging_age_hours,
            envelope=envelope,
            started_at=self.context.started_at,
        )


def _check_init_options(
    config: ApplicationConfig,
    *,
    archive_root: Path,
    archive_id: str | None,
    confirm: bool,
    inspect: bool,
) -> None:
    """Refuse an invocation whose options disagree with each other or with configuration.

    `--archive-root` and `--archive-id` restate what configuration already says.
    The redundancy is the point: initialization is the one irreversible act, so
    it does not take its target or its identity from a file alone
    (`docs/cli.md` §2).
    """
    if confirm and inspect:
        message = (
            "--confirm and --inspect are mutually exclusive: one performs the initialization "
            "and the other exists to prove, without touching anything, that it would be safe"
        )
        raise ConfigurationError.single(message, code="HFARG002")
    if archive_root != config.storage.archive_root:
        message = (
            f"--archive-root {archive_root} does not match storage.archive_root "
            f"{config.storage.archive_root}; the two must name the same directory"
        )
        raise ConfigurationError.single(message, code="HFARG002", location="storage.archive_root")
    if archive_id is not None and archive_id != config.storage.archive_id:
        message = (
            f"--archive-id {archive_id} does not match storage.archive_id "
            f"{config.storage.archive_id}; the sentinel is written with the configured value, "
            f"and a sentinel that disagrees with configuration is fatal and never repaired"
        )
        raise ConfigurationError.single(message, code="HFARG002", location="storage.archive_id")


def _select(config: ApplicationConfig, selectors: list[str] | None) -> tuple[RepositoryConfig, ...]:
    """Resolve selectors against configuration, in configuration order.

    With no selectors the answer is every configured repository. With selectors
    the answer keeps *configuration* order rather than the order they were
    typed, so two invocations naming the same set behave identically — the same
    determinism `docs/architecture.md` §5.3 requires of generated output.

    A selector naming a repository that is not configured is `HFARG004`. All of
    them are reported at once, because an operator who mistyped two names should
    learn both now.
    """
    if not selectors:
        return config.repositories

    # Both sides are `(type, id)`: `RepositoryConfig.key` and
    # `RepositoryIdentity.sort_key` agree by construction.
    wanted = {parse_selector(text).identity.sort_key for text in selectors}
    matched = tuple(repository for repository in config.repositories if repository.key in wanted)
    if missing := wanted - {repository.key for repository in matched}:
        raise ConfigurationError(
            [
                Problem(
                    code="HFARG004",
                    message=(
                        f"selector {repository_type}:{repository_id} names a repository that is "
                        f"not in configuration"
                    ),
                    location=f"{repository_type}:{repository_id}",
                )
                for repository_type, repository_id in sorted(missing)
            ]
        )
    return matched


def _planned(
    client: HubClient,
    repository: RepositoryConfig,
    config: ApplicationConfig,
    *,
    cache_dir: Path,
) -> tuple[dict[str, Any], Problem | None]:
    """Resolve and cost one repository, reporting rather than raising on failure.

    The upstream state is reported in the entry as well as the problem, because
    `HFHUB004`, `HFHUB005`, and `HFHUB001` mean the *repository* is unavailable
    rather than that the run is broken — and every local revision of it is
    preserved regardless (`AD-06`).

    Three Hub calls in the order plan §13.2 puts them: resolve the reference to
    an immutable SHA, enumerate what that revision contains, then cost what
    downloading it would take. Each later call is against the resolved SHA, and a
    failure at any of them leaves the fields below it `null` rather than guessed
    — a partial answer that says which part is missing is more useful than one
    that does not.
    """
    entry: dict[str, Any] = {
        "enabled": repository.enabled,
        "estimated_new_bytes": None,
        "file_count": None,
        "logical_bytes": None,
        "projected_publication_bytes": None,
        "publication_mode": config.storage.publication_mode,
        "repository_id": repository.id,
        "repository_type": repository.type,
        "requested_revision": repository.revision,
        "resolved_commit_sha": None,
        "upstream_state": "unknown",
    }
    identity = RepositoryIdentity.from_config(repository)
    try:
        facts = client.repository(identity, repository.revision)
        entry["resolved_commit_sha"] = facts.commit_sha
        entry["upstream_state"] = "available"

        tree = client.tree(identity, facts.commit_sha)
        entry["file_count"] = len(tree)
        entry["logical_bytes"] = sum(item.size for item in tree)
        entry["projected_publication_bytes"] = projected_publication_bytes(
            entry["logical_bytes"], publication_mode=config.storage.publication_mode
        )

        estimate = client.estimate(
            identity,
            facts.commit_sha,
            cache_dir=cache_dir,
            max_workers=config.sync.max_workers,
        )
        entry["estimated_new_bytes"] = estimate.new_bytes
    except HfcacheError as error:
        problem = error.problems[0]
        entry["upstream_state"] = _UPSTREAM_STATES.get(problem.code, "unreachable")
        return entry, problem
    return entry, None


def _run(  # noqa: PLR0913 - extracted run orchestration preserves domain inputs
    client: HubClient,
    layout: ArchiveLayout,
    config: ApplicationConfig,
    *,
    selected: Sequence[RepositoryConfig],
    envelope: Mapping[str, Any],
    checks: Sequence[Check],
    run_id: RunId,
    started_at: datetime,
) -> RunOutcome:
    """The §7.6 run transaction: open it, reconcile, then do the work.

    Checkpoints 1-3 live here for the same reason the lock and the preflight do:
    `TX-07` requires reconciliation happen under the lock the run already holds
    and **before** the Hub is contacted, and this journal is what proves it did.
    `sync.synchronize` records checkpoints 4-7 and closes the journal.

    The run excludes *itself* from what it reconciles. `TX-01` opened this
    journal before the run was allowed to touch anything, so it is unfinished by
    construction for as long as the run is executing; without the exclusion a
    run would find itself and propose a remedy for work still in progress.
    """
    transaction = open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="sync",
        run_id=run_id,
        archive_id=str(envelope["archive_id"]),
        config_fingerprint=str(envelope["config_fingerprint"]),
    )
    try:
        transaction.checkpoint(
            "run_started",
            archive_id=str(envelope["archive_id"]),
            config_fingerprint=str(envelope["config_fingerprint"]),
            run_id=run_id,
        )
        transaction.checkpoint("preflight_passed", checks=[check.as_entry() for check in checks])
        reconciled = reconcile(
            layout,
            stale_staging_age_hours=config.sync.stale_staging_age_hours,
            envelope=envelope,
            started_at=started_at,
            exclude=(transaction.journal.transaction_id,),
        )
        transaction.checkpoint("journals_reconciled", **reconciled.as_evidence())
        client.require_identity(config.hub.expected_account)
        return synchronize(
            client,
            layout,
            config,
            transaction,
            selected=selected,
            envelope=envelope,
            run_id=run_id,
            started_at=started_at,
        )
    except HfcacheError as error:
        transaction.fail(error.problems[0].code, error.problems[0].message)
        raise


def _named_revision(layout: ArchiveLayout, selector: str) -> Resolved:
    """Resolve `--revision TYPE:ID@SHA` against what the archive retains.

    The SHA is required rather than defaulted to the current revision. `verify
    --revision` is run when a particular revision is under suspicion, and
    silently checking whichever one happens to be current would answer a question
    nobody asked — and would report clean while the damaged revision sat
    unexamined.

    The repository is *not* required to be in configuration. An unmanaged
    repository's data is still the archive's (`AD-06`), and a revision an
    operator is investigating is often one whose repository was removed.
    """
    parsed = parse_selector(selector)
    if parsed.commit_sha is None:
        message = (
            f"--revision {selector!r} names no revision; it takes TYPE:ID@SHA with the full "
            f"40-character commit SHA, because a repository has more than one retained revision"
        )
        raise ConfigurationError.single(message, code="HFARG001", location="--revision")
    return require_retained(layout, parsed.identity, parsed.commit_sha)


def _run_to_verify(layout: ArchiveLayout, run_id: str | None) -> RunReport:
    """The run report `--new` covers: the one named, or the most recent.

    Reports are named `<timestamp>-<run-id>.json`, so lexical order is
    chronological and the newest is found without opening anything. A named run
    still has to be searched for, because the timestamp half of its filename is
    not knowable from the id.

    A report that will not load is skipped while searching for the newest — an
    older readable run is a better answer than a refusal — but a *named* one that
    will not load is reported, because the operator asked for that run and
    silently checking a different one would be the wrong kind of helpful.
    """
    paths = sorted(layout.runs.glob("*.json"), reverse=True)
    for path in paths:
        if run_id is not None and not path.stem.endswith(f"-{run_id}"):
            continue
        try:
            return read_model(path, RunReport, error=IntegrityError, code="HFVER007")
        except HfcacheError:
            if run_id is not None:
                raise
            continue
    message = (
        f"no run report {'named ' + run_id + ' ' if run_id else ''}was found under "
        f"{layout.runs}; `verify --new` checks what a run introduced, so there has to be a run"
    )
    raise ConfigurationError.single(message, code="HFARG004", location=run_id or str(layout.runs))


def _finding_problems(report: VerificationReport) -> list[Problem]:
    """One envelope entry per `(kind, repository)`, carrying how many there were."""
    counted: dict[tuple[str, str, str], int] = {}
    for finding in report.findings:
        key = (finding.kind, finding.repository_type, finding.repository_id)
        counted[key] = counted.get(key, 0) + 1
    return [
        Problem(
            code=FINDING_CODES[kind],
            message=(
                f"{count} {kind} finding{'s' if count > 1 else ''} "
                f"in {repository_type}:{repository_id}"
            ),
            repository=f"{repository_type}:{repository_id}",
            context={"findings": count, "kind": kind},
        )
        for (kind, repository_type, repository_id), count in sorted(counted.items())
    ]


def _plans(layout: ArchiveLayout, wanted: set[str], *, maximum: int) -> tuple[PrunePlan, ...]:
    """Every prune the selected repositories need, in repository order."""
    identities = [
        identity for identity in published_repositories(layout) if identity.selector in wanted
    ]
    return plan_all(layout, identities, maximum=maximum, generated_at=datetime.now(UTC))


def _purge_identities(
    config: ApplicationConfig,
    layout: ArchiveLayout,
    selectors: list[str] | None,
    *,
    all_unmanaged: bool,
) -> tuple[RepositoryIdentity, ...]:
    """Resolve an explicit purge scope and refuse every managed repository."""
    if all_unmanaged and selectors:
        message = "--all-unmanaged and repository selectors are mutually exclusive"
        raise ConfigurationError.single(message, code="HFARG002")
    if not all_unmanaged and not selectors:
        message = "purge requires repository selectors or --all-unmanaged"
        raise ConfigurationError.single(message, code="HFARG003")

    archived = {identity.selector: identity for identity in published_repositories(layout)}
    managed = {
        RepositoryIdentity.from_config(repository).selector for repository in config.repositories
    }
    if all_unmanaged:
        return tuple(
            identity for selector, identity in sorted(archived.items()) if selector not in managed
        )

    parsed = [parse_selector(selector) for selector in selectors or []]
    revision_scoped = [str(selector) for selector in parsed if selector.commit_sha is not None]
    if revision_scoped:
        message = "purge removes whole repositories; revision-qualified selectors are refused"
        raise ConfigurationError.single(message, code="HFARG001", location=revision_scoped[0])
    wanted = {selector.identity.selector for selector in parsed}
    problems = [
        Problem(
            code="HFARG004",
            message=f"selector {selector} names no archived repository",
            location=selector,
        )
        for selector in sorted((wanted - archived.keys()) - managed)
    ]
    problems.extend(
        Problem(
            code="HFARG007",
            message=(
                f"selector {selector} remains in configuration; remove it from configuration "
                "before purging its archive"
            ),
            location=selector,
        )
        for selector in sorted(wanted & managed)
    )
    if problems:
        raise ConfigurationError(problems)
    return tuple(archived[selector] for selector in sorted(wanted))


def _run_envelope(config: ApplicationConfig) -> dict[str, Any]:
    """The provenance fields every durable report carries (`docs/schemas.md` §6)."""
    versions = RuntimeVersions.measured()
    return {
        "application_version": versions.application,
        "archive_id": config.storage.archive_id,
        "config_fingerprint": config.fingerprint(),
        "hostname": socket.gethostname(),
        "huggingface_hub_version": versions.huggingface_hub,
        # Schema 1 describes the execution host only. A daemon's systemd unit
        # does not prove timer/client origin; submitter metadata belongs to the
        # future operation receipt, never a new durable enum (decision 111).
        "invocation_mode": "systemd" if under_systemd() else "interactive",
        "python_version": versions.python,
    }


_UPSTREAM_STATES: Final = {
    "HFHUB004": "missing",
    "HFHUB005": "forbidden",
    "HFHUB006": "refused",
    "HFHUB007": "unresolvable",
}
"""How an upstream failure is described in a per-repository entry.

Distinct from the code because an operator reading `status` or `plan` wants to
know what is true of the repository, not which call reported it. Anything else
is `unreachable`, which is the honest answer when the endpoint itself is the
problem.
"""
