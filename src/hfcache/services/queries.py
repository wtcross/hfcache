"""Local metadata queries shared by CLI, REST, and the later reader (decision 108).

No credentials, Hub clients, locks, or adapter frameworks enter this interface.
References and immutable manifests remain inventory authority (FS-08--FS-16).
"""

import json
import os
import re
import stat
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Protocol

from hfcache.archive import ArchiveInspection, inspect_archive
from hfcache.errors import CodedError, ConfigurationError, HfcacheError, IntegrityError, Problem
from hfcache.identity import (
    REPOSITORY_TYPES,
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    parse_commit_sha,
    parse_publication_id,
    parse_run_id,
    parse_selector,
)
from hfcache.manifests import RevisionManifest
from hfcache.models import Reference, VersionedModel, load
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import (
    VerificationStates,
    published_repositories,
    read_reference,
    read_verification_catalog,
    retained_references,
)
from hfcache.recovery import measure_health
from hfcache.repair import cleanup_warnings, preserved_bytes
from hfcache.reporting import RecoveryReport, RunReport, RuntimeVersions, VerificationReport
from hfcache.services.context import ServiceResult
from hfcache.storage import read_model
from hfcache.verification import estimate_verification

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from hfcache.config import ApplicationConfig, RepositoryConfig


@dataclass(frozen=True, slots=True)
class RepositoryQuery:
    """A local inventory scope; selector SHA handling retains CLI compatibility."""

    selectors: tuple[str, ...] = ()
    repository_type: str | None = None
    revisions: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "selectors", tuple(self.selectors))
        for selector in self.selectors:
            parse_selector(selector)
        if self.repository_type is not None and self.repository_type not in REPOSITORY_TYPES:
            message = (
                f"--type must be one of {', '.join(sorted(REPOSITORY_TYPES))}; "
                f"{self.repository_type!r} is neither"
            )
            raise ConfigurationError.single(message, code="HFARG002", location="--type")


@dataclass(frozen=True, slots=True)
class PublicationQuery:
    """One exact publication; an absent instance never falls back to current (FS-12)."""

    identity: RepositoryIdentity
    commit_sha: CommitSha
    publication_id: PublicationId

    def __post_init__(self) -> None:
        try:
            parse_commit_sha(self.commit_sha, code="HFARG001")
            parse_publication_id(self.publication_id, code="HFARG001")
        except CodedError as exc:
            raise ConfigurationError.single(str(exc), code=exc.code) from exc


ALL_REPOSITORIES = RepositoryQuery()


class MetadataQueries(Protocol):
    """Read-only capability: no command, credential resolver, or Hub authority."""

    def version(self) -> ServiceResult: ...

    def inspect_archive(self) -> ArchiveInspection: ...

    def archive_status(self, request: RepositoryQuery = ALL_REPOSITORIES) -> ServiceResult: ...

    def list_repositories(self, request: RepositoryQuery = ALL_REPOSITORIES) -> ServiceResult: ...

    def estimate_verification(self) -> ServiceResult: ...

    def list_reports(self) -> tuple[str, ...]: ...

    def read_report(self, run_id: str) -> RunReport | RecoveryReport | VerificationReport: ...

    def read_reference(
        self, identity: RepositoryIdentity, commit_sha: str | None = None
    ) -> Reference: ...

    def read_manifest(self, request: PublicationQuery) -> RevisionManifest: ...


def query_version() -> ServiceResult:
    """Report the installed stack without reading configuration or archive state."""
    versions = RuntimeVersions.measured()
    backend = "http"
    if find_spec("hf_xet") is not None:
        try:
            backend = f"xet {package_version('hf-xet')}"
        except PackageNotFoundError:  # pragma: no cover - broken installation
            backend = "xet unknown"
    return ServiceResult(
        "version",
        {
            "application": versions.application,
            "huggingface_hub": versions.huggingface_hub,
            "python": versions.python,
            "transfer_backend": backend,
        },
    )


def validate_config(config: ApplicationConfig, *, token_source: str) -> ServiceResult:
    """Describe already validated policy and nonsecret credential source.

    Credential resolution belongs to the trusted execution boundary; the read
    capability never receives the resolver or token (AD-21, decision 108).
    """
    return ServiceResult(
        "config validate",
        {
            "config_fingerprint": config.fingerprint(),
            "enabled_repositories": len(config.enabled_repositories),
            "repositories": len(config.repositories),
            "token_source": token_source,
        },
    )


@dataclass(frozen=True, slots=True)
class LocalQueries:
    """Metadata orchestration over a frozen installed archive policy."""

    config: ApplicationConfig

    @property
    def layout(self) -> ArchiveLayout:
        """Compute the validated archive layout without touching it."""
        return ArchiveLayout(root=self.config.storage.archive_root)

    def version(self) -> ServiceResult:
        """Report installed versions independently of archive health."""
        return query_version()

    def inspect_archive(self) -> ArchiveInspection:
        """Inspect initialization state without mount probes or mutation."""
        return inspect_archive(self.layout, archive_id=self.config.storage.archive_id)

    def archive_status(self, request: RepositoryQuery = ALL_REPOSITORIES) -> ServiceResult:
        """Report configured and archived unmanaged repositories using local truth."""
        layout = self.layout
        configured = {
            RepositoryIdentity.from_config(repository): repository
            for repository in self.config.repositories
        }
        published = published_repositories(layout)
        identities = tuple(configured) + tuple(item for item in published if item not in configured)
        selected = _scope(identities, request)
        last_run = _last_run_statuses(layout)
        states = VerificationStates.of(layout)
        entries = [
            _status_entry(layout, identity, configured.get(identity), last_run, states)
            for identity in selected
        ]
        archive: dict[str, Any] = {
            "archive_id": self.config.storage.archive_id,
            "root": str(layout.root),
        }
        warnings: list[Problem] = []
        try:
            health = measure_health(
                layout,
                self.config.storage,
                stale_staging_age_hours=self.config.sync.stale_staging_age_hours,
            )
        except HfcacheError:
            archive["reachable"] = False
        else:
            archive["reachable"] = True
            archive |= health.as_payload()
            warnings.extend(health.reconciliation.warnings)
            warnings.extend(cleanup_warnings(layout))
            archive["quarantined_bytes"] = preserved_bytes(layout)
        archive["verification"] = _verification_health(layout)
        return ServiceResult(
            "status", {"archive": archive, "repositories": entries}, tuple(warnings)
        )

    def list_repositories(self, request: RepositoryQuery = ALL_REPOSITORIES) -> ServiceResult:
        """List authoritative published inventory, including unmanaged repositories."""
        layout = self.layout
        configured = {
            RepositoryIdentity.from_config(repository): repository
            for repository in self.config.repositories
        }
        published = published_repositories(layout)
        # Validate against both sets even though list only returns archived rows.
        _scope(
            tuple(configured) + tuple(item for item in published if item not in configured), request
        )
        selected = _scope(published, request, require_present=False)
        states = VerificationStates.of(layout)
        return ServiceResult(
            "list",
            {
                "repositories": [
                    _listed(
                        layout,
                        identity,
                        configured.get(identity),
                        states,
                        revisions=request.revisions,
                    )
                    for identity in selected
                ]
            },
        )

    def estimate_verification(self) -> ServiceResult:
        """Estimate with stat only: no hashing, writes, lock, or confidence increase."""
        return ServiceResult("verify --estimate", estimate_verification(self.layout).as_payload())

    def list_reports(self) -> tuple[str, ...]:
        """List validated report IDs in reverse chronological filename order."""
        return tuple(run_id for _, run_id in _report_paths(self.layout))

    def read_report(self, run_id: str) -> RunReport | RecoveryReport | VerificationReport:
        """Read one uniquely named report and check filename, body, and archive identity."""
        try:
            checked = parse_run_id(run_id, code="HFARG001")
        except CodedError as exc:
            raise ConfigurationError.single(str(exc), code=exc.code) from exc
        paths = [path for path, found in _report_paths(self.layout) if found == checked]
        if not paths:
            msg = "no run report has this id"
            raise ConfigurationError.single(msg, code="HFARG004", location=run_id)
        if len(paths) != 1:
            msg = "multiple reports claim the same run id"
            raise IntegrityError.single(msg, code="HFVER007", location=run_id)
        path = paths[0]
        raw = _read_bytes(self.layout, path, code="HFVER007")
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            msg = "run report is malformed JSON"
            raise IntegrityError.single(msg, code="HFVER007", location=run_id) from exc
        model: type[RunReport] | type[RecoveryReport] | type[VerificationReport] = RunReport
        if isinstance(payload, dict):
            command = payload.get("command")
            if isinstance(command, str) and command.startswith("verify"):
                model = VerificationReport
            elif isinstance(command, str) and command.startswith("recover"):
                model = RecoveryReport
        report = load(model, raw, error=IntegrityError, code="HFVER007", location=run_id)
        expected = self.layout.run_report(report.started_at, checked)
        if (
            report.run_id != checked
            or path != expected
            or report.archive_id != self.config.storage.archive_id
        ):
            msg = "run report identity disagrees with requested archive/run"
            raise IntegrityError.single(
                msg,
                code="HFVER007",
                location=run_id,
            )
        return report

    def read_reference(
        self, identity: RepositoryIdentity, commit_sha: str | None = None
    ) -> Reference:
        """Read one current/per-SHA ref, pinning its canonical publication locators."""
        repository = self.layout.repository(identity)
        try:
            sha = parse_commit_sha(commit_sha, code="HFARG001") if commit_sha is not None else None
        except CodedError as exc:
            raise ConfigurationError.single(str(exc), code=exc.code) from exc
        path = repository.revision_ref(sha) if sha is not None else repository.current_ref
        reference = _read_evidence(self.layout, path, Reference, code="HFVER008")
        if reference.identity != identity or (sha is not None and reference.commit_sha != sha):
            msg = "reference identity disagrees with requested repository/revision"
            raise IntegrityError.single(msg, code="HFVER008")
        request = PublicationQuery(
            identity, CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
        )
        if str(reference.tree) != str(
            repository.tree_reference(request.commit_sha, request.publication_id)
        ) or str(reference.manifest) != str(
            repository.manifest_reference(request.commit_sha, request.publication_id)
        ):
            msg = "reference locators disagree with publication identity"
            raise IntegrityError.single(msg, code="HFVER008")
        manifest = self.read_manifest(request)
        if manifest.publication_generation != reference.publication_generation:
            msg = "reference and manifest generations disagree"
            raise IntegrityError.single(msg, code="HFVER008")
        if sha is None:
            retained = self.read_reference(identity, reference.commit_sha)
            if retained.model_dump(exclude={"updated_at"}) != reference.model_dump(
                exclude={"updated_at"}
            ):
                message = "current reference disagrees with the retained per-SHA reference"
                raise IntegrityError.single(message, code="HFVER008")
        return reference

    def read_manifest(self, request: PublicationQuery) -> RevisionManifest:
        """Read the exact instance requested, including a retained repair predecessor."""
        repository = self.layout.repository(request.identity)
        manifest = _read_evidence(
            self.layout,
            repository.manifest(request.commit_sha, request.publication_id),
            RevisionManifest,
            code="HFVER007",
        )
        if (
            manifest.repository_type != request.identity.type
            or manifest.repository_id != request.identity.id
            or manifest.commit_sha != request.commit_sha
            or manifest.publication_id != request.publication_id
            or str(manifest.tree)
            != str(repository.manifest_tree_field(request.commit_sha, request.publication_id))
        ):
            msg = "manifest identity disagrees with requested publication"
            raise IntegrityError.single(msg, code="HFVER007")
        _require_directory(
            self.layout,
            repository.instance(request.commit_sha, request.publication_id),
            code="HFVER008",
        )
        return manifest


def _scope(
    identities: tuple[RepositoryIdentity, ...],
    request: RepositoryQuery,
    *,
    require_present: bool = True,
) -> tuple[RepositoryIdentity, ...]:
    wanted = {parse_selector(text).identity for text in request.selectors}
    if require_present and (missing := wanted - set(identities)):
        raise ConfigurationError(
            [
                Problem(
                    code="HFARG004",
                    message=(
                        f"selector {identity.selector} names no configured or archived repository"
                    ),
                    location=identity.selector,
                )
                for identity in sorted(missing, key=lambda item: item.sort_key)
            ]
        )
    return tuple(
        identity
        for identity in identities
        if (not wanted or identity in wanted)
        and (request.repository_type is None or identity.type == request.repository_type)
    )


_REPORT_NAME = re.compile(r"[0-9]{8}T[0-9]{6}Z-([0-9a-f]{32})[.]json")


def _report_paths(layout: ArchiveLayout) -> tuple[tuple[Path, str], ...]:
    return tuple(
        (path, match[1])
        for path in sorted(layout.runs.glob("*.json"), reverse=True)
        if (match := _REPORT_NAME.fullmatch(path.name)) is not None
    )


def _open_contained(layout: ArchiveLayout, path: Path, *, directory: bool, code: str) -> int:
    """Open beneath the archive by dirfd, rejecting every symlink, including races.

    Opening each component with O_NOFOLLOW prevents path swaps from turning a
    metadata query into an arbitrary host read (FS-09/FS-15, decision 108).
    """
    descriptor: int | None = None
    try:
        relative = path.relative_to(layout.root)
        descriptor = os.open(layout.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for index, part in enumerate(relative.parts):
            is_directory = index < len(relative.parts) - 1 or directory
            flags = (
                os.O_RDONLY | os.O_NOFOLLOW | (os.O_DIRECTORY if is_directory else os.O_NONBLOCK)
            )
            following = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        expected = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected(os.fstat(descriptor).st_mode):
            msg = "metadata path has an unexpected file type"
            raise IntegrityError.single(msg, code=code)
    except (OSError, ValueError) as exc:
        msg = "metadata path is absent, unsafe, or unreadable"
        raise IntegrityError.single(
            msg,
            code=code,
            location=str(layout.archive_relative(path)),
        ) from exc
    else:
        result = descriptor
        descriptor = None
        return result
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_bytes(layout: ArchiveLayout, path: Path, *, code: str) -> bytes:
    descriptor = _open_contained(layout, path, directory=False, code=code)
    try:
        with os.fdopen(descriptor, "rb") as stream:
            return stream.read()
    except OSError as exc:
        message = "metadata artifact could not be read"
        raise IntegrityError.single(
            message, code=code, location=str(layout.archive_relative(path))
        ) from exc


def _require_directory(layout: ArchiveLayout, path: Path, *, code: str) -> None:
    os.close(_open_contained(layout, path, directory=True, code=code))


def _read_evidence[ModelT: VersionedModel](
    layout: ArchiveLayout, path: Path, model: type[ModelT], *, code: str
) -> ModelT:
    return load(
        model,
        _read_bytes(layout, path, code=code),
        error=IntegrityError,
        code=code,
        location=str(layout.archive_relative(path)),
    )


def _verification_health(layout: ArchiveLayout) -> dict[str, Any]:
    """The archive's verification headline, as `docs/cli.md` §2 requires of `status`.

    `degraded` is the one an operator acts on, and it stays true until a
    verification re-reads the objects that failed or a repair replaces them
    (`docs/schemas.md` §5.2) — never merely because a later narrow run did not
    look. `status` still exits `0`: it reports, and `verify` is what classifies.

    An archive with no verification catalog reports `degraded = false` with no
    last full verification, which is the truth about an archive nothing has
    verified yet rather than a claim that it is sound.
    """
    catalog = read_verification_catalog(layout)
    if catalog is None:
        return {"degraded": False, "last_full_verification": None, "outstanding_failures": 0}
    return {
        "degraded": catalog.is_degraded,
        "last_full_verification": (
            catalog.last_full_verification.model_dump(mode="json")
            if catalog.last_full_verification
            else None
        ),
        "outstanding_failures": len(catalog.outstanding_failures),
    }


def _status_entry(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    repository: RepositoryConfig | None,
    last_run: Mapping[str, str],
    states: VerificationStates,
) -> dict[str, Any]:
    """One repository's local truth, from its references and the last run report.

    Read from the references rather than from the catalog, for the same reason
    `list` does: the catalog is derived and can be missing (`FS-16`), and this is
    the command an operator runs when something is already wrong. An archive that
    holds nothing for this repository answers with zeros rather than failing —
    a repository configured but never synced is a normal state, not an error.

    `upstream_state` stays `unknown`. `status` never contacts the Hub, because it
    must answer when the Hub is unreachable; `plan` is the command that resolves.
    """
    entry: dict[str, Any] = {
        "current_commit_sha": None,
        "current_publication_generation": None,
        "enabled": repository.enabled if repository else None,
        "last_run_status": last_run.get(identity.selector),
        "managed": repository is not None,
        "repository_id": identity.id,
        "repository_type": identity.type,
        "requested_revision": repository.revision if repository else None,
        "retained_generations": [],
        "retained_revisions": 0,
        "upstream_state": "unknown",
        "verification_state": "unverified",
    }
    try:
        held = retained_references(layout, identity)
        current = RepositoryLayout(archive=layout, identity=identity).current_ref
        reference = read_reference(layout, current) if current.exists() else None
    except HfcacheError:
        return entry
    entry["retained_revisions"] = len(held)
    entry["retained_generations"] = [item.publication_generation for item in held]
    if reference is not None:
        entry["current_commit_sha"] = reference.commit_sha
        entry["current_publication_generation"] = reference.publication_generation
        # The current revision's state, from the one place any of it is recorded
        # (decision 51). A revision nothing has verified offline reads
        # `unverified`, which is what makes `verified` mean something.
        entry["verification_state"] = states.state_of(
            identity, reference.commit_sha, reference.publication_id
        )
    return entry


def _last_run_statuses(layout: ArchiveLayout) -> dict[str, str]:
    """What the most recent run report said about each repository.

    The newest report by name, which is chronological: `run_report` stamps the
    UTC start time first, so lexical order is time order and no file has to be
    opened to find the latest one.

    A run report that will not load is skipped rather than reported. It is
    informational here — the references above are the archive's truth — and
    `status` exists to answer even when parts of the archive are damaged.

    `glob` on a directory that is absent or unreadable yields nothing rather
    than raising, so an archive that is not mounted answers "no last run",
    which is the truthful answer and not an error.
    """
    for path in sorted(layout.runs.glob("*.json"), reverse=True):
        try:
            report = read_model(path, RunReport, error=IntegrityError, code="HFVER007")
        except HfcacheError:
            continue
        return {
            f"{result.repository_type}:{result.repository_id}": result.status
            for result in report.repositories
        }
    return {}


def _listed(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    configured: RepositoryConfig | None,
    states: VerificationStates,
    *,
    revisions: bool,
) -> dict[str, Any]:
    """One repository's inventory, read from its references and manifests."""
    repository = RepositoryLayout(archive=layout, identity=identity)
    held = retained_references(layout, identity)
    current = (
        read_reference(layout, repository.current_ref) if repository.current_ref.exists() else None
    )
    entry: dict[str, Any] = {
        "current_commit_sha": current.commit_sha if current else None,
        "current_publication_id": current.publication_id if current else None,
        "enabled": configured.enabled if configured else None,
        "managed": configured is not None,
        "repository_id": identity.id,
        "repository_type": identity.type,
        "retained_revisions": len(held),
    }
    if revisions:
        entry["revisions"] = [
            _listed_revision(repository, reference, identity, states) for reference in held
        ]
    return entry


def _listed_revision(
    repository: RepositoryLayout,
    reference: Reference,
    identity: RepositoryIdentity,
    states: VerificationStates,
) -> dict[str, Any]:
    """One retained revision, from the immutable manifest that describes it."""
    manifest = read_model(
        repository.manifest(
            CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
        ),
        RevisionManifest,
        error=IntegrityError,
        code="HFVER007",
    )
    return {
        "commit_sha": manifest.commit_sha,
        "file_count": manifest.file_count,
        "publication_generation": manifest.publication_generation,
        "publication_id": manifest.publication_id,
        "published_at": manifest.published_at.isoformat().replace("+00:00", "Z"),
        "total_bytes": manifest.total_bytes,
        "verification_state": states.state_of(
            identity, manifest.commit_sha, manifest.publication_id
        ),
    }
