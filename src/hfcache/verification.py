"""Reading the archive back, and saying whether it is what the manifests claim.

Plan §16. Verification is the one operation that treats the archive as suspect:
every other module writes what it has just proved, and this one re-reads what
something else wrote — possibly months ago, possibly across a snapshot restore,
possibly after a ZFS checksum error. So the manifest is the expectation and the
filesystem is the observation, never the other way round.

Three rules shape everything here.

**A finding changes nothing.** Plan §16.1's last line is the whole stance: a
later verification mismatch never rewrites the expected digest, auto-prunes the
revision, or silently re-downloads over the evidence (`AD-13`, `AD-18`). This
module has no write path at all. It returns findings; what to do about them is
`repair`'s question and an operator's decision.

**Reading is expensive, so each physical object is read once.** Plan §16.2 item
4 builds the read set from current `(device, inode)` identity confirmed by
`samefile`, so a blob hardlinked into five retained revisions costs one read
rather than five. In copy mode nothing is shared — two identical files in two
trees are two physical objects — so every file is read even when the expected
digests match.

**One repository's damage never hides another's.** A reference that will not
load, a manifest that fails validation, a tree that is not there: each is a
finding attributed to the revision it belongs to, and the run continues. `verify`
is what an operator reaches for when the archive is already known to be wrong
(`docs/architecture.md` §7.9), so aborting at the first broken artifact would
withhold exactly the report they came for.

The division of labour with `hfcache.sync` is worth stating. Ingestion hashing
(`sync.hash_snapshot`) reads the *Hub cache* before a tree exists and decides
what a manifest will claim. This module reads the *published tree* and decides
whether that claim still holds. They share `ObjectIdentity` because "which
physical object is this" has one right answer, and nothing else.
"""

import os
import stat
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final, Literal, final

from hfcache.errors import ConfigurationError, HfcacheError, IntegrityError
from hfcache.hashing import sha256_file
from hfcache.identity import COMMIT_SHA_LENGTH, CommitSha, PublicationId, RepositoryIdentity
from hfcache.manifests import FileEntry, RevisionManifest
from hfcache.paths import RepositoryLayout, parse_repository_relative, resolve_within
from hfcache.publication import read_reference
from hfcache.reporting import Finding, VerificationReport, VerificationScope
from hfcache.storage import read_model
from hfcache.sync import ObjectIdentity

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from hfcache.hashing import FileDigest
    from hfcache.models import Reference
    from hfcache.paths import ArchiveLayout
    from hfcache.reporting import RunReport

__all__ = [
    "FINDING_CODES",
    "INTRODUCING_STATUSES",
    "ReadSet",
    "Resolved",
    "VerificationOutcome",
    "VerificationTarget",
    "build_report",
    "require_retained",
    "resolve_repository",
    "resolve_revision",
    "resolve_run",
    "verify_target",
    "verify_targets",
]

FINDING_CODES: Final[Mapping[str, str]] = {
    "digest_mismatch": "HFVER001",
    "size_mismatch": "HFVER002",
    "missing": "HFVER003",
    "extra": "HFVER004",
    "not_regular": "HFVER005",
    "unreadable": "HFVER006",
    "manifest_invalid": "HFVER007",
    "ref_invalid": "HFVER008",
}
"""Which `docs/cli.md` §5.4 code each finding kind reports.

One table, so the kind an operator reads in the report and the code a scheduler
matches on cannot drift. `tests/unit/test_verification.py` checks it against both
`Finding.kind`'s literals and the code table parsed out of `docs/cli.md`.
"""

INTRODUCING_STATUSES: Final = frozenset({"published", "completed_with_warnings"})
"""Run-report statuses that introduced content `verify --new` must read.

`skipped` observed nothing new. `ref_moved_to_retained_revision` moved the
current pointer onto bytes an earlier run already published. `failed` and
`disabled` published nothing at all. Only these two put new files on the dataset,
which is what "content introduced by one run" means (`docs/cli.md` §2).
"""


# --------------------------------------------------------------------------- #
# The read set (plan §16.2 item 4)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class _ReadObject:
    """One physical object this run has already read, and where it read it."""

    digest: FileDigest
    path: Path


@final
@dataclass(slots=True)
class ReadSet:
    """Every physical object read so far, so none is read twice.

    Mutable by design: it accumulates as the run proceeds, and it is the run's
    accounting of what verification actually cost. `unique_bytes_read` and
    `unique_objects_read` in the report come from here rather than from summing
    manifest sizes, so they describe reads that happened rather than reads that
    were planned.

    Sharing is decided per file by the caller, because it is a property of how
    that file was *published* rather than of how this archive is configured now.
    A hardlink-mode tree and a copy-mode tree can both be retained — a
    `publication_mode` change is one of plan §16.3's reasons to run a full
    verification — and each has to be read the way its own bytes are laid out.
    """

    objects: dict[ObjectIdentity, _ReadObject] = field(default_factory=dict, repr=False)
    bytes_read: int = 0
    objects_read: int = 0

    def digest_of(self, path: Path, *, share: bool) -> FileDigest:
        """Hash one published file, reusing a read only when it is provably the same object.

        `share = False` is copy mode and always reads: two files with identical
        expected digests in two copy-mode trees are two physical objects, and
        reading one of them would prove nothing about the other
        (`docs/schemas.md` §7).

        `share = True` looks the object up by its current `(device, inode)` and
        then *confirms* with `samefile` rather than trusting the tuple. The
        confirmation is not ceremony: an inode number is reused by the filesystem
        after deletion, so a recorded identity whose original path is gone may now
        name entirely different bytes. When the confirmation fails the object is
        read again, which is the answer that cannot be wrong.
        """
        if not share:
            return self._read(path)
        identity = ObjectIdentity.of(path)
        known = self.objects.get(identity)
        if known is not None and _still_one_object(known.path, path):
            return known.digest
        digest = self._read(path)
        self.objects[identity] = _ReadObject(digest=digest, path=path)
        return digest

    def _read(self, path: Path) -> FileDigest:
        """Stream one object and account for it."""
        digest = sha256_file(path, error=IntegrityError, code="HFVER006")
        self.bytes_read += digest.size
        self.objects_read += 1
        return digest


def _still_one_object(recorded: Path, candidate: Path) -> bool:
    """Whether an earlier read's path and this one are one file right now.

    `Path.samefile` stats both, so it answers about the filesystem as it is
    rather than about a tuple captured earlier. A recorded path that has since
    been unlinked raises, and the honest answer to "is this the same object" when
    one of them cannot be found is no.
    """
    try:
        return recorded.samefile(candidate)
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# What is being verified
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class VerificationTarget:
    """One retained publication instance, with everything needed to check it.

    The reference and the manifest together, for the same reason retention needs
    both: the reference says which instance of a SHA is active, and the manifest
    says what that instance is supposed to contain. Verifying the manifest of an
    instance no reference names would be verifying something no consumer reaches.
    """

    identity: RepositoryIdentity
    reference: Reference
    manifest: RevisionManifest
    tree: Path

    @property
    def share_reads(self) -> bool:
        """Whether this instance's files may be read once and shared.

        Hardlink publication points several trees at one blob, so one read
        answers for all of them. Copy publication does not, and plan §16.2 item 4
        is explicit that copy-mode files are each read.
        """
        return self.manifest.publication_mode == "hardlink"

    def finding(self, kind: str, **fields: object) -> Finding:
        """Build a finding already attributed to this instance."""
        return _finding(
            self.identity,
            commit_sha=self.reference.commit_sha,
            kind=kind,
            publication_id=self.reference.publication_id,
            **fields,
        )


def _finding(
    identity: RepositoryIdentity,
    *,
    commit_sha: str,
    kind: str,
    publication_id: str | None,
    **fields: object,
) -> Finding:
    """One finding, attributed to a repository and a revision.

    `publication_id` is `None` only for a reference that would not load: such a
    reference names no instance, so there is no publication to attribute the
    finding to and inventing one would be a claim this module cannot support
    (decision 49).
    """
    return Finding.model_validate(
        {
            "commit_sha": commit_sha,
            "kind": kind,
            "publication_id": publication_id,
            "repository_id": identity.id,
            "repository_type": identity.type,
            **fields,
        }
    )


@final
@dataclass(frozen=True, slots=True)
class Resolved:
    """A revision ready to verify, the findings that stopped it, or neither.

    All three are real answers. A `target` is the ordinary case. Findings without
    a target is an artifact too damaged to read — the finding *is* the result for
    that revision. Neither means nothing is retained under that SHA, which
    `verify --new` meets whenever a later prune rotated out what the run it is
    checking had published.
    """

    target: VerificationTarget | None = None
    findings: tuple[Finding, ...] = ()


def resolve_revision(
    layout: ArchiveLayout, identity: RepositoryIdentity, commit_sha: CommitSha
) -> Resolved:
    """Load one retained revision's reference and manifest, or report why not.

    The per-SHA reference is the entry point rather than the revision directory,
    because `refs/revisions/<sha>.json` is what makes a SHA retained (`FS-11`)
    and a directory can additionally hold a superseded repair instance inside its
    grace period. Verifying the retired instance would report an archive as
    degraded for holding evidence it was told to keep.
    """
    repository = RepositoryLayout(archive=layout, identity=identity)
    path = repository.revision_ref(commit_sha)
    # `is_file` rather than `exists`: both follow symlinks, and what matters is
    # that a regular reference file is there to read. A symlink pointing at one
    # is still readable and still the archive's own artifact, so it is not
    # refused here — `doctor` check `HFMNT015` is where an unexpected file type
    # at an application-owned path is reported.
    if not path.is_file():
        return Resolved()
    try:
        reference = read_reference(layout, path)
    except HfcacheError as error:
        return Resolved(
            findings=(
                _finding(
                    identity,
                    commit_sha=commit_sha,
                    kind="ref_invalid",
                    publication_id=None,
                    observed=_reason(error, "the reference"),
                ),
            )
        )
    return _resolve_reference(layout, identity, reference)


def _resolve_reference(
    layout: ArchiveLayout, identity: RepositoryIdentity, reference: Reference
) -> Resolved:
    """Turn a loaded reference into a target, or into the findings that stopped it."""
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(reference.commit_sha)
    publication = PublicationId(reference.publication_id)
    tree = repository.instance(commit, publication)
    findings: list[Finding] = []

    if not tree.is_dir():
        findings.append(
            _reference_finding(
                identity,
                reference,
                "ref_invalid",
                f"the reference names {layout.archive_relative(tree)}, which is not a directory",
            )
        )
    try:
        manifest = read_model(
            repository.manifest(commit, publication),
            RevisionManifest,
            error=IntegrityError,
            code="HFVER007",
        )
    except HfcacheError as error:
        findings.append(
            _reference_finding(
                identity, reference, "manifest_invalid", _reason(error, "the manifest")
            )
        )
        return Resolved(findings=tuple(findings))

    findings.extend(_agreement_findings(identity, reference, manifest))
    if findings:
        return Resolved(findings=tuple(findings))
    return Resolved(
        target=VerificationTarget(
            identity=identity, reference=reference, manifest=manifest, tree=tree
        )
    )


def _reference_finding(
    identity: RepositoryIdentity, reference: Reference, kind: str, observed: str
) -> Finding:
    """A finding about the instance a valid reference names."""
    return _finding(
        identity,
        commit_sha=reference.commit_sha,
        kind=kind,
        publication_id=reference.publication_id,
        observed=observed,
    )


def _agreement_findings(
    identity: RepositoryIdentity, reference: Reference, manifest: RevisionManifest
) -> list[Finding]:
    """Refuse a manifest that does not describe the instance the reference names.

    The manifest loaded, so its own arithmetic is sound; what is checked here is
    that it belongs where it was found. A manifest filed under one SHA that
    describes another is `manifest_invalid` rather than a set of per-file
    mismatches, because every file in it would then be compared against the wrong
    expectation and the resulting report would be noise.
    """
    mismatched = [
        f"{name} {observed!r} where {expected!r} was expected"
        for name, expected, observed in (
            ("commit_sha", reference.commit_sha, manifest.commit_sha),
            ("publication_id", reference.publication_id, manifest.publication_id),
            ("repository_id", identity.id, manifest.repository_id),
            ("repository_type", identity.type, manifest.repository_type),
        )
        if expected != observed
    ]
    if not mismatched:
        return []
    return [
        _reference_finding(
            identity,
            reference,
            "manifest_invalid",
            "the manifest does not describe the instance the reference names: "
            + "; ".join(mismatched),
        )
    ]


def _reason(error: HfcacheError, what: str) -> str:
    """Render why a durable artifact could not be used, for a finding's `observed`."""
    return f"{what} could not be read: " + "; ".join(problem.message for problem in error.problems)


def resolve_repository(layout: ArchiveLayout, identity: RepositoryIdentity) -> tuple[Resolved, ...]:
    """Every retained revision of one repository, in commit-SHA order.

    Enumerated from `refs/revisions/` one file at a time rather than through
    `publication.retained_references`, which loads the whole set and raises on
    the first reference that will not parse. Here a broken reference has to be a
    finding about *that* revision while the others are still verified, which is
    only possible if each is read on its own.

    A file in that directory whose name is not a commit SHA names no revision, so
    there is no revision to report a finding about and it is left alone — the
    same stance `publication.published_repositories` takes toward a directory
    whose name is not an identifier (`FS-19`).
    """
    repository = RepositoryLayout(archive=layout, identity=identity)
    resolved: list[Resolved] = []
    for path in sorted((repository.refs / "revisions").glob("*.json")):
        if not _is_commit_sha(path.stem):
            continue
        resolved.append(resolve_revision(layout, identity, CommitSha(path.stem)))
    return tuple(resolved)


def _is_commit_sha(value: str) -> bool:
    """Whether a reference file's name is a full lowercase commit SHA."""
    return len(value) == COMMIT_SHA_LENGTH and all(
        character in "0123456789abcdef" for character in value
    )


def resolve_run(layout: ArchiveLayout, report: RunReport) -> tuple[Resolved, ...]:
    """Every revision one run introduced and the archive still retains.

    Resolution goes through the references rather than through the publication
    ids the run recorded, because those describe the archive as it was and this
    describes the archive as it is. Two consequences, both correct. A revision a
    later prune rotated out is not verified — nothing retains it, so there is
    nothing to check. A revision a later repair replaced is verified in its
    *replacement* instance, which is what consumers now read.
    """
    return tuple(
        resolve_revision(
            layout,
            RepositoryIdentity.of(result.repository_type, result.repository_id),
            CommitSha(result.resolved_commit_sha),
        )
        for result in report.repositories
        if result.status in INTRODUCING_STATUSES and result.resolved_commit_sha is not None
    )


def require_retained(
    layout: ArchiveLayout, identity: RepositoryIdentity, commit_sha: CommitSha
) -> Resolved:
    """Resolve one named revision, refusing a SHA the archive does not retain.

    `verify --revision` names a revision an operator believes is there. When it
    is not, the useful answer is that the selector names nothing — a mistyped SHA
    is an invocation problem — rather than exit `40`, which would tell a scheduler
    the archive is corrupt because somebody typed one wrong character.
    """
    resolved = resolve_revision(layout, identity, commit_sha)
    if resolved.target is None and not resolved.findings:
        message = (
            f"{identity.selector}@{commit_sha} names a revision this archive does not retain; "
            f"`hfcache list --revisions` reports the retained set"
        )
        raise ConfigurationError.single(
            message, code="HFARG004", location=f"{identity.selector}@{commit_sha}"
        )
    return resolved


# --------------------------------------------------------------------------- #
# Checking one instance (plan §16.2 items 6 and 7)
# --------------------------------------------------------------------------- #


def verify_target(target: VerificationTarget, reads: ReadSet) -> tuple[Finding, ...]:
    """Compare one published instance against the manifest that describes it.

    Every manifest path is checked for presence, type, size, and digest, and the
    tree is then walked for anything the manifest does not list. Both directions
    are needed and neither implies the other: a truncated file is invisible to a
    path-set comparison, and an injected file is invisible to a per-entry check.

    At most one finding per path. A file whose size is already wrong is not
    hashed — the digest would differ too, and reporting both would double the
    apparent damage while adding nothing an operator can act on.
    """
    findings = [
        finding
        for entry in target.manifest.files
        for finding in _entry_findings(target, entry, reads)
    ]
    findings.extend(_extra_findings(target))
    return tuple(findings)


def _entry_findings(target: VerificationTarget, entry: FileEntry, reads: ReadSet) -> list[Finding]:
    """Check one manifest entry against the file it claims."""
    path = resolve_within(target.tree, entry.path, code="HFVER007")
    try:
        # `lstat`, not `stat`: the question is what is *at* this name. A symlink
        # to a valid file would satisfy `stat` while being something publication
        # never creates (`AD-10`), and reporting it as `not_regular` is what tells
        # an operator the tree was edited rather than that a file is fine.
        info = path.lstat()
    except FileNotFoundError:
        return [target.finding("missing", path=entry.path, expected=entry.sha256)]
    except OSError as exc:
        return [target.finding("unreadable", path=entry.path, observed=str(exc.strerror))]
    if shape := _shape_findings(target, entry, info):
        return shape
    return _digest_findings(target, entry, path, reads)


def _shape_findings(
    target: VerificationTarget, entry: FileEntry, info: os.stat_result
) -> list[Finding]:
    """What `stat` alone can settle: the file's type, then its length.

    Both are cheap and both make hashing pointless. A path that is a directory or
    a symlink is not the object the manifest describes at all, and a regular file
    of the wrong length cannot hash to the expected digest — reporting the digest
    too would double the apparent damage while adding nothing to act on.
    """
    if not stat.S_ISREG(info.st_mode):
        return [
            target.finding(
                "not_regular",
                path=entry.path,
                expected="regular file",
                observed=_describe_type(info.st_mode),
            )
        ]
    if info.st_size != entry.size:
        return [
            target.finding(
                "size_mismatch",
                path=entry.path,
                expected=str(entry.size),
                observed=str(info.st_size),
            )
        ]
    return []


def _digest_findings(
    target: VerificationTarget, entry: FileEntry, path: Path, reads: ReadSet
) -> list[Finding]:
    """Read the object and compare what it hashes to with what was published."""
    try:
        digest = reads.digest_of(path, share=target.share_reads)
    except HfcacheError as error:
        return [
            target.finding(
                "unreadable",
                path=entry.path,
                observed="; ".join(problem.message for problem in error.problems),
            )
        ]
    if digest.digest != entry.sha256:
        return [
            target.finding(
                "digest_mismatch",
                path=entry.path,
                expected=entry.sha256,
                observed=digest.digest,
            )
        ]
    return []


def _describe_type(mode: int) -> str:
    """Name the file type found where a regular file was expected."""
    for name, predicate in (
        ("directory", stat.S_ISDIR),
        ("symbolic link", stat.S_ISLNK),
        ("FIFO", stat.S_ISFIFO),
        ("socket", stat.S_ISSOCK),
        ("block device", stat.S_ISBLK),
        ("character device", stat.S_ISCHR),
    ):
        if predicate(mode):
            return name
    return f"file type {stat.S_IFMT(mode):#o}"  # pragma: no cover - POSIX defines no seventh


def _extra_findings(target: VerificationTarget) -> list[Finding]:
    """Report anything in the tree the manifest does not list (`HFVER004`).

    Directories are checked too, against the set of parents the manifest's own
    paths imply. An unexpected directory is reported once and not descended into:
    everything inside it is unexpected by construction, and listing every one of
    them would bury the finding that matters under the noise it caused.

    A directory standing where the manifest lists a *file* is not reported here.
    The per-entry check already reported it as `not_regular`, which is the finding
    that describes what happened; reporting it a second time under a different
    kind would make one act look like two.

    `followlinks=False` so a symlink to a directory is never walked. It is still
    *reported*, either as an extra entry here or as `not_regular` when the
    manifest lists that path, which is what keeps a link planted in the tree from
    being followed out of the archive.
    """
    listed = {PurePosixPath(entry.path) for entry in target.manifest.files}
    implied = {parent for path in listed for parent in path.parents}
    findings: list[Finding] = []
    for root, directories, files in os.walk(target.tree, followlinks=False):
        here = PurePosixPath(os.path.relpath(root, target.tree))
        findings.extend(
            _extra_finding(target, here / name)
            for name in sorted(files)
            if here / name not in listed
        )
        findings.extend(
            _extra_finding(target, here / name)
            for name in sorted(directories)
            if here / name not in implied and here / name not in listed
        )
        directories[:] = [name for name in sorted(directories) if here / name in implied]
    return findings


def _extra_finding(target: VerificationTarget, relative: PurePosixPath) -> Finding:
    """One path the tree holds and the manifest does not list.

    A name the repository-relative grammar refuses cannot go in the `path` field,
    which is typed by that grammar — so it is reported in `observed` instead and
    the finding is still made. A file this archive could never have published is
    exactly the kind of thing an operator needs told about.
    """
    text = str(relative)
    try:
        parse_repository_relative(text)
    except ValueError:
        return target.finding(
            "extra", observed=f"{text!r} is not a path this archive could have published"
        )
    return target.finding("extra", path=text)


# --------------------------------------------------------------------------- #
# One whole run
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class VerificationOutcome:
    """What one `verify` invocation read, and what it found."""

    findings: tuple[Finding, ...]
    repositories: int
    revisions: int
    bytes_read: int
    objects_read: int
    started_at: datetime
    completed_at: datetime

    @property
    def outcome(self) -> Literal["clean", "failed"]:
        """Whether anything was found. A clean run has no findings."""
        return "failed" if self.findings else "clean"

    @property
    def duration_seconds(self) -> float:
        """How long the run took, from its own timestamps."""
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def throughput_bytes_per_second(self) -> float:
        """Measured sequential read rate, or zero when nothing was read.

        Zero rather than a computed figure for a run that read nothing:
        `verify --new` after an idempotent sync legitimately has no bytes to
        read, and dividing by an elapsed time that rounds to zero would report a
        rate no storage ever achieved. The estimator treats zero as "not
        measured" for exactly that reason.
        """
        elapsed = self.duration_seconds
        if elapsed <= 0.0 or self.bytes_read == 0:
            return 0.0
        return self.bytes_read / elapsed

    @property
    def codes(self) -> tuple[str, ...]:
        """Every distinct `HFVER###` this run has to report, in code order."""
        return tuple(sorted({FINDING_CODES[finding.kind] for finding in self.findings}))


def verify_targets(
    resolved: Sequence[Resolved], *, started_at: datetime, now: datetime | None = None
) -> VerificationOutcome:
    """Verify everything that resolved, and account for what it cost.

    `repositories` counts distinct repositories rather than revisions, because
    "two repositories, seven revisions" is how plan §16.4 and `docs/schemas.md`
    §7 describe a scope and how an operator sizes the next run.

    A revision that could not be resolved still counts toward `revisions`: the
    run did look at it, and a report covering fewer revisions than it reported
    findings for would be internally inconsistent. A SHA the archive no longer
    retains counts toward neither, because nothing was there to look at.
    """
    reads = ReadSet()
    findings: list[Finding] = []
    repositories: set[tuple[str, str]] = set()
    revisions = 0
    for item in resolved:
        findings.extend(item.findings)
        repositories.update(
            (finding.repository_type, finding.repository_id) for finding in item.findings
        )
        if item.target is not None:
            repositories.add(item.target.identity.sort_key)
            findings.extend(verify_target(item.target, reads))
        if item.target is not None or item.findings:
            revisions += 1
    return VerificationOutcome(
        findings=tuple(sorted(findings, key=lambda finding: finding.sort_key)),
        repositories=len(repositories),
        revisions=revisions,
        bytes_read=reads.bytes_read,
        objects_read=reads.objects_read,
        started_at=started_at,
        completed_at=now or datetime.now(UTC),
    )


def build_report(
    outcome: VerificationOutcome,
    *,
    envelope: Mapping[str, object],
    command: str,
    mode: Literal["new", "full", "revision"],
    run_id: str,
) -> VerificationReport:
    """Render one verification as the durable artifact `docs/schemas.md` §7 defines.

    The exit classification is derived from the findings rather than passed in,
    so a report can never claim a clean archive while listing findings — the
    model refuses that combination, and deriving it here means no caller can
    construct the refusal in the first place.
    """
    failed = bool(outcome.findings)
    return VerificationReport.model_validate(
        dict(envelope)
        | {
            "command": command,
            "completed_at": outcome.completed_at,
            "errors": outcome.codes,
            "exit_code": int(IntegrityError.exit_code) if failed else 0,
            "findings": outcome.findings,
            "mode": mode,
            "outcome": "failed" if failed else "success",
            "run_id": run_id,
            "scope": VerificationScope(
                repositories=outcome.repositories,
                revisions=outcome.revisions,
                unique_bytes_read=outcome.bytes_read,
                unique_objects_read=outcome.objects_read,
            ),
            "started_at": outcome.started_at,
            "throughput_bytes_per_second": outcome.throughput_bytes_per_second,
            "verification_outcome": outcome.outcome,
        }
    )
