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
    RunId,
    parse_commit_sha,
    parse_publication_id,
    parse_run_id,
    parse_selector,
)
from hfcache.manifests import RevisionManifest
from hfcache.metadata import UNBOUNDED, MetadataEntry, MetadataReader, QueryBounds, QueryLimitError
from hfcache.models import Reference, VersionedModel, load
from hfcache.paths import ArchiveLayout
from hfcache.publication import (
    VerificationStates,
)
from hfcache.recovery import measure_health
from hfcache.repair import cleanup_warnings, preserved_bytes
from hfcache.reporting import (
    Finding,
    RecoveryReport,
    RunReport,
    RuntimeVersions,
    VerificationCatalog,
    VerificationReport,
)
from hfcache.services.context import ServiceResult
from hfcache.verification import Resolved, VerificationTarget, estimate_resolved

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
    bounds: QueryBounds = UNBOUNDED

    @property
    def layout(self) -> ArchiveLayout:
        """Compute the validated archive layout without touching it."""
        return ArchiveLayout(root=self.config.storage.archive_root)

    def version(self) -> ServiceResult:
        """Report installed versions independently of archive health."""
        return query_version()

    def inspect_archive(self) -> ArchiveInspection:
        """Inspect initialization state without mount probes or mutation."""
        return inspect_archive(
            self.layout,
            archive_id=self.config.storage.archive_id,
            reader=MetadataReader(self.layout.root, self.bounds),
        )

    def archive_status(self, request: RepositoryQuery = ALL_REPOSITORIES) -> ServiceResult:
        """Report configured and archived unmanaged repositories using local truth."""
        layout = self.layout
        configured = {
            RepositoryIdentity.from_config(repository): repository
            for repository in self.config.repositories
        }
        reader = MetadataReader(layout.root, self.bounds)
        published = _published_repositories(layout, reader)
        identities = tuple(configured) + tuple(item for item in published if item not in configured)
        selected = _scope(identities, request)
        last_run = _last_run_statuses(self, reader)
        catalog = _verification_catalog(layout, reader)
        states = _verification_states(catalog)
        entries = [
            _status_entry(self, identity, configured.get(identity), last_run, states, reader)
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
                reader=reader,
            )
            pending_warnings = cleanup_warnings(layout, reader=reader)
            quarantined_bytes = preserved_bytes(layout, reader=reader)
        except QueryLimitError:
            raise
        except HfcacheError, OSError, ValueError:
            archive["reachable"] = False
        else:
            archive["reachable"] = True
            archive |= health.as_payload()
            warnings.extend(health.reconciliation.warnings)
            warnings.extend(pending_warnings)
            archive["quarantined_bytes"] = quarantined_bytes
        archive["verification"] = _verification_health(catalog)
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
        reader = MetadataReader(layout.root, self.bounds)
        published = _published_repositories(layout, reader)
        # Validate against both sets even though list only returns archived rows.
        _scope(
            tuple(configured) + tuple(item for item in published if item not in configured), request
        )
        selected = _scope(published, request, require_present=False)
        states = _verification_states(_verification_catalog(layout, reader))
        return ServiceResult(
            "list",
            {
                "repositories": [
                    _listed(
                        self,
                        identity,
                        configured.get(identity),
                        states,
                        reader=reader,
                        revisions=request.revisions,
                    )
                    for identity in selected
                ]
            },
        )

    def estimate_verification(self) -> ServiceResult:
        """Estimate with stat only: no hashing, writes, lock, or confidence increase."""
        reader = MetadataReader(self.layout.root, self.bounds)
        resolved = []
        for identity in _published_repositories(self.layout, reader):
            repository = self.layout.repository(identity)
            damaged_revisions = set()
            for entry in _entries(reader, repository.refs / "revisions"):
                if not re.fullmatch(r"[0-9a-f]{40}[.]json", entry.path.name):
                    continue
                reference = None
                try:
                    reference = _raw_reference(self, identity, entry.path, reader, entry.path.stem)
                    request = PublicationQuery(
                        identity,
                        CommitSha(reference.commit_sha),
                        PublicationId(reference.publication_id),
                    )
                    manifest = self._manifest(request, reader)
                    if manifest.publication_generation != reference.publication_generation:
                        message = "reference and manifest generations disagree"
                        raise IntegrityError.single(message, code="HFVER008")
                    target = VerificationTarget(
                        identity,
                        reference,
                        manifest,
                        repository.instance(request.commit_sha, request.publication_id),
                    )
                except IntegrityError:
                    if reference is None:
                        damaged_revisions.add(entry.path.stem)
                    resolved.append(
                        Resolved(
                            findings=(
                                Finding.model_validate(
                                    {
                                        "repository_type": identity.type,
                                        "repository_id": identity.id,
                                        "commit_sha": entry.path.stem,
                                        "publication_id": None,
                                        "kind": "ref_invalid",
                                        "observed": "revision metadata is unreadable",
                                    }
                                ),
                            )
                        )
                    )
                else:
                    resolved.append(Resolved(target=target))
            try:
                _current(self, identity, reader)
            except IntegrityError:
                # A broken per-SHA reference already contributes one revision.
                # A readable current ref pointing to that same damaged artifact
                # must not count it again (the verifier's VER-008 convention).
                try:
                    current = _raw_reference(self, identity, repository.current_ref, reader)
                except IntegrityError:
                    pass
                else:
                    if current.commit_sha in damaged_revisions:
                        continue
                resolved.append(
                    Resolved(
                        findings=(
                            Finding.model_validate(
                                {
                                    "repository_type": identity.type,
                                    "repository_id": identity.id,
                                    "commit_sha": None,
                                    "publication_id": None,
                                    "kind": "ref_invalid",
                                    "observed": "current reference is unreadable or inconsistent",
                                }
                            ),
                        )
                    )
                )
        catalog = _verification_catalog(self.layout, reader)
        return ServiceResult(
            "verify --estimate",
            estimate_resolved(tuple(resolved), catalog=catalog, stat_file=reader.stat).as_payload(),
        )

    def list_reports(self) -> tuple[str, ...]:
        """List validated report IDs in reverse chronological filename order."""
        paths = _report_paths(self.layout, MetadataReader(self.layout.root, self.bounds))
        identifiers = tuple(run_id for _, run_id in paths)
        if len(set(identifiers)) != len(identifiers):
            msg = "duplicate report identities"
            raise IntegrityError.single(msg, code="HFVER007")
        return identifiers

    def read_report(self, run_id: str) -> RunReport | RecoveryReport | VerificationReport:
        """Read one uniquely named report and check filename, body, and archive identity."""
        try:
            checked = parse_run_id(run_id, code="HFARG001")
        except CodedError as exc:
            raise ConfigurationError.single(str(exc), code=exc.code) from exc
        reader = MetadataReader(self.layout.root, self.bounds)
        paths = [path for path, found in _report_paths(self.layout, reader) if found == checked]
        if not paths:
            msg = "no run report has this id"
            raise ConfigurationError.single(msg, code="HFARG004", location=run_id)
        if len(paths) != 1:
            msg = "multiple reports claim the same run id"
            raise IntegrityError.single(msg, code="HFVER007", location=run_id)
        path = paths[0]
        raw = _read_bytes(self.layout, path, code="HFVER007", reader=reader)
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
        return self._reference(identity, commit_sha, MetadataReader(self.layout.root, self.bounds))

    def _reference(
        self, identity: RepositoryIdentity, commit_sha: str | None, reader: MetadataReader
    ) -> Reference:
        repository = self.layout.repository(identity)
        try:
            sha = parse_commit_sha(commit_sha, code="HFARG001") if commit_sha is not None else None
        except CodedError as exc:
            raise ConfigurationError.single(str(exc), code=exc.code) from exc
        path = repository.revision_ref(sha) if sha is not None else repository.current_ref
        reference = _read_evidence(self.layout, path, Reference, code="HFVER008", reader=reader)
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
        manifest = self._manifest(request, reader)
        if manifest.publication_generation != reference.publication_generation:
            msg = "reference and manifest generations disagree"
            raise IntegrityError.single(msg, code="HFVER008")
        if sha is None:
            retained = self._reference(identity, reference.commit_sha, reader)
            if retained.model_dump(exclude={"updated_at"}) != reference.model_dump(
                exclude={"updated_at"}
            ):
                message = "current reference disagrees with the retained per-SHA reference"
                raise IntegrityError.single(message, code="HFVER008")
        return reference

    def read_manifest(self, request: PublicationQuery) -> RevisionManifest:
        """Read the exact instance requested, including a retained repair predecessor."""
        return self._manifest(request, MetadataReader(self.layout.root, self.bounds))

    def _manifest(self, request: PublicationQuery, reader: MetadataReader) -> RevisionManifest:
        repository = self.layout.repository(request.identity)
        manifest = _read_evidence(
            self.layout,
            repository.manifest(request.commit_sha, request.publication_id),
            RevisionManifest,
            code="HFVER007",
            reader=reader,
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
            reader=reader,
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


def _entries(reader: MetadataReader, path: Path) -> tuple[MetadataEntry, ...]:
    try:
        return reader.entries(path)
    except (OSError, ValueError) as exc:
        msg = "metadata directory is unsafe or unreadable"
        raise IntegrityError.single(msg, code="HFVER007") from exc


def _report_paths(layout: ArchiveLayout, reader: MetadataReader) -> tuple[tuple[Path, str], ...]:
    found = []
    for entry in _entries(reader, layout.runs):
        if (match := _REPORT_NAME.fullmatch(entry.path.name)) is not None:
            if not stat.S_ISREG(entry.info.st_mode):
                msg = "report is not an ordinary file"
                raise IntegrityError.single(msg, code="HFVER007")
            found.append((entry.path, match[1]))
    return tuple(reversed(found))


def _read_bytes(
    layout: ArchiveLayout, path: Path, *, code: str, reader: MetadataReader | None = None
) -> bytes:
    try:
        return (reader or MetadataReader(layout.root)).read(path)
    except (OSError, ValueError) as exc:
        msg = "metadata artifact is absent, unsafe, or unreadable"
        raise IntegrityError.single(msg, code=code) from exc


def _require_directory(
    layout: ArchiveLayout, path: Path, *, code: str, reader: MetadataReader | None = None
) -> None:
    try:
        os.close((reader or MetadataReader(layout.root)).open(path, directory=True))
    except (OSError, ValueError) as exc:
        msg = "publication directory is absent or unsafe"
        raise IntegrityError.single(msg, code=code) from exc


def _read_evidence[ModelT: VersionedModel](
    layout: ArchiveLayout,
    path: Path,
    model: type[ModelT],
    *,
    code: str,
    reader: MetadataReader | None = None,
) -> ModelT:
    return load(
        model, _read_bytes(layout, path, code=code, reader=reader), error=IntegrityError, code=code
    )


def _verification_catalog(
    layout: ArchiveLayout, reader: MetadataReader
) -> VerificationCatalog | None:
    try:
        catalog = _read_evidence(
            layout, layout.verification_catalog, VerificationCatalog, code="HFVER007", reader=reader
        )
    except IntegrityError:
        return None
    return catalog


def _verification_states(catalog: VerificationCatalog | None) -> VerificationStates:
    return VerificationStates(
        outcomes={
            (
                repository.repository_type,
                repository.repository_id,
                revision.commit_sha,
                revision.publication_id,
            ): revision.outcome
            for repository in (catalog.repositories if catalog else ())
            for revision in repository.revisions
            if revision.publication_id is not None
        }
    )


def _verification_health(catalog: VerificationCatalog | None) -> dict[str, Any]:
    """The archive's verification headline, as `docs/cli.md` §2 requires of `status`.

    `degraded` is the one an operator acts on, and it stays true until a
    verification re-reads the objects that failed or a repair replaces them
    (`docs/schemas.md` §5.2) — never merely because a later narrow run did not
    look. `status` still exits `0`: it reports, and `verify` is what classifies.

    An archive with no verification catalog reports `degraded = false` with no
    last full verification, which is the truth about an archive nothing has
    verified yet rather than a claim that it is sound.
    """
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


def _status_entry(  # noqa: PLR0913, PLR0917 - one status projection capability
    queries: LocalQueries,
    identity: RepositoryIdentity,
    repository: RepositoryConfig | None,
    last_run: Mapping[str, str],
    states: VerificationStates,
    reader: MetadataReader,
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
        held = _retained(queries, identity, reader)
        reference = _current(queries, identity, reader)
    except QueryLimitError:
        raise
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
        try:
            manifest = queries._manifest(  # noqa: SLF001 - shared module implementation
                PublicationQuery(
                    identity,
                    CommitSha(reference.commit_sha),
                    PublicationId(reference.publication_id),
                ),
                reader,
            )
        except IntegrityError:
            pass
        else:
            if manifest.publication_generation == reference.publication_generation:
                entry["verification_state"] = states.state_of(
                    identity, reference.commit_sha, reference.publication_id
                )
    return entry


def _last_run_statuses(queries: LocalQueries, reader: MetadataReader) -> dict[str, str]:
    try:
        paths = _report_paths(queries.layout, reader)
    except IntegrityError:
        return {}
    for path, run_id in paths:
        try:
            report = _read_evidence(queries.layout, path, RunReport, code="HFVER007", reader=reader)
            if (
                report.archive_id != queries.config.storage.archive_id
                or report.run_id != run_id
                or path != queries.layout.run_report(report.started_at, RunId(report.run_id))
            ):
                continue
        except IntegrityError:
            continue
        return {
            f"{item.repository_type}:{item.repository_id}": item.status
            for item in report.repositories
        }
    return {}


def _published_repositories(
    layout: ArchiveLayout, reader: MetadataReader
) -> tuple[RepositoryIdentity, ...]:
    found = []
    for repository_type, directory in (("model", "models"), ("dataset", "datasets")):
        for namespace in _entries(reader, layout.repos / directory):
            if not stat.S_ISDIR(namespace.info.st_mode):
                if stat.S_ISLNK(namespace.info.st_mode):
                    msg = "repository namespace is a symlink"
                    raise IntegrityError.single(msg, code="HFVER008")
                continue
            for name in _entries(reader, namespace.path):
                if not stat.S_ISDIR(name.info.st_mode):
                    if stat.S_ISLNK(name.info.st_mode):
                        msg = "repository directory is a symlink"
                        raise IntegrityError.single(msg, code="HFVER008")
                    continue
                try:
                    found.append(
                        RepositoryIdentity.of(
                            repository_type, f"{namespace.path.name}/{name.path.name}"
                        )
                    )
                except ValueError:
                    continue
    return tuple(sorted(found, key=lambda item: item.sort_key))


def _raw_reference(
    queries: LocalQueries,
    identity: RepositoryIdentity,
    path: Path,
    reader: MetadataReader,
    sha: str | None = None,
) -> Reference:
    reference = _read_evidence(queries.layout, path, Reference, code="HFVER008", reader=reader)
    repository = queries.layout.repository(identity)
    if (
        reference.identity != identity
        or (sha is not None and reference.commit_sha != sha)
        or str(reference.tree)
        != str(
            repository.tree_reference(
                CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
            )
        )
        or str(reference.manifest)
        != str(
            repository.manifest_reference(
                CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
            )
        )
    ):
        msg = "reference identity or locators disagree"
        raise IntegrityError.single(msg, code="HFVER008")
    return reference


def _retained(
    queries: LocalQueries, identity: RepositoryIdentity, reader: MetadataReader
) -> tuple[Reference, ...]:
    found = []
    for entry in _entries(reader, queries.layout.repository(identity).refs / "revisions"):
        if entry.path.suffix != ".json":
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", entry.path.stem):
            msg = "retained reference has an invalid identity"
            raise IntegrityError.single(msg, code="HFVER008")
        found.append(_raw_reference(queries, identity, entry.path, reader, entry.path.stem))
    return tuple(sorted(found, key=lambda item: item.publication_generation))


def _current(
    queries: LocalQueries, identity: RepositoryIdentity, reader: MetadataReader
) -> Reference | None:
    repository = queries.layout.repository(identity)
    try:
        reader.stat(repository.current_ref)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        msg = "current reference is unsafe"
        raise IntegrityError.single(msg, code="HFVER008") from exc
    current = _raw_reference(queries, identity, repository.current_ref, reader)
    retained = _raw_reference(
        queries,
        identity,
        repository.revision_ref(CommitSha(current.commit_sha)),
        reader,
        current.commit_sha,
    )
    if current.model_dump(exclude={"updated_at"}) != retained.model_dump(exclude={"updated_at"}):
        msg = "current and retained references disagree"
        raise IntegrityError.single(msg, code="HFVER008")
    return current


def _listed(  # noqa: PLR0913 - one inventory projection capability
    queries: LocalQueries,
    identity: RepositoryIdentity,
    configured: RepositoryConfig | None,
    states: VerificationStates,
    *,
    reader: MetadataReader,
    revisions: bool,
) -> dict[str, Any]:
    """One repository's inventory, read from its references and manifests."""
    held = _retained(queries, identity, reader)
    current = _current(queries, identity, reader)
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
            _listed_revision(queries, reference, identity, states, reader) for reference in held
        ]
    return entry


def _listed_revision(
    queries: LocalQueries,
    reference: Reference,
    identity: RepositoryIdentity,
    states: VerificationStates,
    reader: MetadataReader,
) -> dict[str, Any]:
    """One retained revision, from the immutable manifest that describes it."""
    manifest = queries._manifest(  # noqa: SLF001 - shared module implementation
        PublicationQuery(
            identity, CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
        ),
        reader,
    )
    if manifest.publication_generation != reference.publication_generation:
        msg = "reference and manifest generations disagree"
        raise IntegrityError.single(msg, code="HFVER008")
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
