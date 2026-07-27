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
from hfcache.identity import (
    COMMIT_SHA_LENGTH,
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    RunId,
)
from hfcache.manifests import FileEntry, RevisionManifest
from hfcache.paths import RepositoryLayout, parse_repository_relative, resolve_within
from hfcache.publication import (
    publish_verification_catalog,
    published_repositories,
    read_reference,
    read_verification_catalog,
)
from hfcache.reporting import (
    Finding,
    FullVerificationSummary,
    OutstandingFailure,
    RepositoryVerificationEntry,
    VerificationCatalog,
    VerificationReport,
    VerificationRevisionEntry,
    VerificationScope,
)
from hfcache.storage import read_model, write_model
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
    "REPORT_MODE",
    "RUNS_MODE",
    "UNDETECTABLE",
    "ReadSet",
    "Resolved",
    "RevisionOutcome",
    "VerificationEstimate",
    "VerificationOutcome",
    "VerificationTarget",
    "build_report",
    "estimate_verification",
    "persist_verification",
    "require_retained",
    "resolve_archive",
    "resolve_current_reference",
    "resolve_repository",
    "resolve_revision",
    "resolve_run",
    "retained_keys",
    "verification_catalog",
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
    commit_sha: str | None,
    kind: str,
    publication_id: str | None,
    **fields: object,
) -> Finding:
    """One finding, attributed to a repository and a revision.

    `publication_id` is `None` only for a reference that would not load: such a
    reference names no instance, so there is no publication to attribute the
    finding to and inventing one would be a claim this module cannot support
    (decision 49). `commit_sha` is `None` only for a `current.json` that would
    not parse (`VER-009`): it names no revision either, and unlike a per-SHA
    reference its filename carries no SHA to fall back on.
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


def resolve_current_reference(
    layout: ArchiveLayout, identity: RepositoryIdentity
) -> tuple[Finding, ...]:
    """Check `refs/current.json` against the retained set (`VER-008`).

    Verification enumerates `refs/revisions/`, because that is what makes a SHA
    retained (`FS-11`). `current.json` is not in that set, and until now nothing
    read it — so the **one file a consumer must read** (§6.3) was the one artifact
    a full verification never looked at, while plan §16.2 step 3 said it
    validated refs. A `current.json` naming an instance that does not exist is
    `FS-10`'s dangling reference, it strands every consumer that resolves it, and
    `verify --full` called the archive clean.

    `docs/schemas.md` §4.2 states the invariant this enforces: `current.json`
    always names a SHA that also has a `refs/revisions/<sha>.json`, and both agree
    on `publication_id`.

    A repository with no `current.json` is not a finding — nothing has completed a
    publication there yet. A `current.json` that will not parse at all *is* one
    (`VER-009`): the one file a consumer must read is unreadable, which is damage
    to report, not a state to infer around. It names no revision and no instance,
    so the finding carries a null `commit_sha` and `publication_id` — attributing
    the damage to a retained revision that may be perfectly sound would assert
    exactly what the unreadable reference failed to say.
    """
    repository = RepositoryLayout(archive=layout, identity=identity)
    if not repository.current_ref.is_file():
        return ()
    try:
        current = read_reference(layout, repository.current_ref)
    except HfcacheError as error:
        return (
            _finding(
                identity,
                commit_sha=None,
                kind="ref_invalid",
                publication_id=None,
                observed=_reason(error, "the current reference"),
            ),
        )

    retained = repository.revision_ref(CommitSha(current.commit_sha))
    if not retained.is_file():
        return (
            _reference_finding(
                identity,
                current,
                "ref_invalid",
                f"current.json names {current.commit_sha}, which the archive does not retain: "
                f"there is no {layout.archive_relative(retained)}",
            ),
        )
    try:
        active = read_reference(layout, retained)
    except HfcacheError:
        # The per-SHA reference is the damaged artifact and `resolve_revision`
        # reports it against its own SHA. A second finding here would describe one
        # broken file twice, which is the noise `_agreement_findings` avoids for
        # the same reason.
        return ()
    if active.publication_id == current.publication_id:
        # They agree, so anything else wrong with that instance belongs to the
        # revision, and `resolve_revision` has already looked at it.
        return ()
    return (
        _reference_finding(
            identity,
            current,
            "ref_invalid",
            f"current.json names instance {current.publication_id} but "
            f"refs/revisions/{current.commit_sha}.json names {active.publication_id}; "
            f"they must agree (`docs/schemas.md` §4.2)",
        ),
    )


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
    # `current.json` is not in `refs/revisions/`, so nothing above reaches it
    # (`VER-008`). It is reported as its own entry rather than folded into the
    # revision it names, because what is wrong is the reference, not the bytes.
    if current := resolve_current_reference(layout, identity):
        resolved.append(Resolved(findings=current))
    return tuple(resolved)


def _is_commit_sha(value: str) -> bool:
    """Whether a reference file's name is a full lowercase commit SHA."""
    return len(value) == COMMIT_SHA_LENGTH and all(
        character in "0123456789abcdef" for character in value
    )


def resolve_archive(layout: ArchiveLayout) -> tuple[Resolved, ...]:
    """Every retained revision of every repository the archive holds (plan §16.2).

    The repository set is read off `published/repos/` rather than off
    configuration, because those are different sets and the difference matters
    most here: removing a repository from configuration never deletes its
    archive (`AD-06`), and a quarterly verification that skipped unmanaged
    repositories would leave exactly the content nothing else touches unchecked.
    """
    return tuple(
        resolved
        for identity in published_repositories(layout)
        for resolved in resolve_repository(layout, identity)
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
class RevisionOutcome:
    """One revision this run covered, and how it came out.

    Carried through the run rather than collapsed into a finding list, because
    `catalog/verification.json` records an outcome *per revision* — and "this
    revision was re-read and was clean" is a fact no set of findings can express,
    findings being what a clean revision does not produce.

    `commit_sha` is `None` for the one coverage the run makes that is not a
    revision: a `current.json` that would not parse (`VER-009`). Such an outcome
    still counts toward the scope — the run did look — but it never becomes a
    per-revision catalog entry, because an outcome attributed to no revision
    raises nobody's confidence.
    """

    commit_sha: str | None
    findings: tuple[Finding, ...]
    identity: RepositoryIdentity
    publication_id: str | None

    @property
    def outcome(self) -> Literal["clean", "failed"]:
        """Whether this revision came out clean."""
        return "failed" if self.findings else "clean"


@final
@dataclass(frozen=True, slots=True)
class VerificationOutcome:
    """What one `verify` invocation read, and what it found."""

    revisions_covered: tuple[RevisionOutcome, ...]
    bytes_read: int
    objects_read: int
    started_at: datetime
    completed_at: datetime

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Every finding the run made, in the order `docs/schemas.md` §7 fixes."""
        return tuple(
            sorted(
                (finding for revision in self.revisions_covered for finding in revision.findings),
                key=lambda finding: finding.sort_key,
            )
        )

    @property
    def repositories(self) -> int:
        """Distinct repositories looked at.

        Counted separately from revisions because "two repositories, seven
        revisions" is how plan §16.4 and `docs/schemas.md` §7 describe a scope,
        and how an operator sizes the next run.
        """
        return len({revision.identity.sort_key for revision in self.revisions_covered})

    @property
    def revisions(self) -> int:
        """Revisions looked at, including ones too damaged to read.

        A revision that could not be resolved still counts: the run did look at
        it, and a report covering fewer revisions than it reported findings for
        would be internally inconsistent. A SHA the archive no longer retains
        counts toward neither, because nothing was there to look at.
        """
        return len(self.revisions_covered)

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

    One `RevisionOutcome` per revision the run *covered*, which is what the
    verification catalog is updated from: a revision this run re-read and found
    clean has to be distinguishable from one it never looked at, and only the
    covered set can make that distinction.
    """
    reads = ReadSet()
    covered = [
        _revision_outcome(item, reads)
        for item in resolved
        if item.target is not None or item.findings
    ]
    return VerificationOutcome(
        revisions_covered=tuple(covered),
        bytes_read=reads.bytes_read,
        objects_read=reads.objects_read,
        started_at=started_at,
        completed_at=now or datetime.now(UTC),
    )


def _revision_outcome(item: Resolved, reads: ReadSet) -> RevisionOutcome:
    """Verify one resolved revision, or record the findings that stopped it."""
    if item.target is None:
        # An artifact too damaged to read still belongs to a revision, and the
        # findings themselves say which — they were built from the reference
        # path and the repository directory that led to it.
        first = item.findings[0]
        return RevisionOutcome(
            commit_sha=first.commit_sha,
            findings=item.findings,
            identity=RepositoryIdentity.of(first.repository_type, first.repository_id),
            publication_id=first.publication_id,
        )
    return RevisionOutcome(
        commit_sha=item.target.reference.commit_sha,
        findings=verify_target(item.target, reads),
        identity=item.target.identity,
        publication_id=item.target.reference.publication_id,
    )


# --------------------------------------------------------------------------- #
# Estimation (plan §16.4)
# --------------------------------------------------------------------------- #

UNDETECTABLE: Final = "undetectable"
"""What the writer can say about NAS maintenance windows (decision 50)."""


@final
@dataclass(frozen=True, slots=True)
class VerificationEstimate:
    """What a full verification would cost, measured without reading anything.

    Plan §16.4's field set. `measured_throughput_bytes_per_second` is `None`
    until a full verification has actually run, and the estimated duration is
    `None` with it — a number derived from a rate nobody measured would be a
    guess wearing a decimal point, and the operator scheduling a quarterly job
    against a NAS maintenance window is exactly the person who should not be
    given one.
    """

    repositories: int
    revisions: int
    unique_objects: int
    unique_bytes: int
    unreadable_objects: int
    measured_throughput_bytes_per_second: float | None

    @property
    def estimated_duration_seconds(self) -> float | None:
        """How long the read would take at the last measured rate, if there is one."""
        if not self.measured_throughput_bytes_per_second:
            return None
        return self.unique_bytes / self.measured_throughput_bytes_per_second

    def as_payload(self) -> dict[str, object]:
        """Render for `verify --estimate`'s `data` payload (`docs/cli.md` §4.1)."""
        return {
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "measured_throughput_bytes_per_second": self.measured_throughput_bytes_per_second,
            "mode": "estimate",
            "repositories": self.repositories,
            "revisions": self.revisions,
            "storage_maintenance": UNDETECTABLE,
            "unique_bytes": self.unique_bytes,
            "unique_objects": self.unique_objects,
            "unreadable_objects": self.unreadable_objects,
        }


def estimate_verification(layout: ArchiveLayout) -> VerificationEstimate:
    """Cost a full verification with `stat` alone (plan §16.4).

    Nothing is hashed and nothing is opened, so this is cheap enough to run
    before deciding whether tonight is the night. The unique set is built the
    same way the read set is — by `(device, inode)` for a hardlink-published
    instance, and per file for a copy-published one — so the figure it reports is
    the figure `--full` would actually read rather than the archive's logical
    size.

    A path that cannot be stat'ed contributes no bytes and is counted separately.
    It costs nothing to read because there is nothing there, and `--full` will
    report it as `missing` or `unreadable`; saying so here means an operator
    reading a suspiciously small estimate knows why it is small.

    The last measured throughput comes from `catalog/verification.json`, which
    only a completed `--full` writes. Before the first one there is no rate and
    therefore no duration.
    """
    resolved = resolve_archive(layout)
    repositories: set[tuple[str, str]] = set()
    seen: set[object] = set()
    unique_bytes = 0
    unreadable = 0
    revisions = 0
    for item in resolved:
        repositories.update(
            (finding.repository_type, finding.repository_id) for finding in item.findings
        )
        if item.target is None:
            revisions += 1 if item.findings else 0
            continue
        repositories.add(item.target.identity.sort_key)
        revisions += 1
        for entry in item.target.manifest.files:
            path = resolve_within(item.target.tree, entry.path, code="HFVER007")
            try:
                info = path.lstat()
            except OSError:
                unreadable += 1
                continue
            key = (
                ObjectIdentity(device=info.st_dev, inode=info.st_ino)
                if item.target.share_reads
                # A copy-published file is its own physical object even when
                # another tree holds identical bytes, so it is keyed by where it
                # is rather than by what it is.
                else (item.target.reference.publication_id, entry.path)
            )
            if key in seen:
                continue
            seen.add(key)
            unique_bytes += info.st_size

    catalog = read_verification_catalog(layout)
    last = catalog.last_full_verification if catalog else None
    return VerificationEstimate(
        repositories=len(repositories),
        revisions=revisions,
        unique_objects=len(seen),
        unique_bytes=unique_bytes,
        unreadable_objects=unreadable,
        measured_throughput_bytes_per_second=(
            last.throughput_bytes_per_second if last and last.throughput_bytes_per_second else None
        ),
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


# --------------------------------------------------------------------------- #
# Persistence (plan §16.2 items 8 and 9)
# --------------------------------------------------------------------------- #

RUNS_MODE: Final = 0o700
REPORT_MODE: Final = 0o600
"""`runs/` is the writer's own record and is never consumer-visible (§5.2)."""


def persist_verification(
    layout: ArchiveLayout,
    report: VerificationReport,
    outcome: VerificationOutcome,
    *,
    mode: Literal["new", "full", "revision"],
) -> Path:
    """Write the report, then the catalog that names it (plan §16.2 items 8-9).

    In that order, because the catalog's `last_full_verification.report` is a
    path an operator follows. A catalog naming a report that had not been written
    yet would be a dangling reference in the one artifact an operator reaches for
    when they already suspect the archive.

    Both writes are atomic renames of derived or append-only files, which is why
    `--new` and `--revision` can do this without the lock `--full` holds: a
    concurrent reader sees one whole catalog or the other, and a run report's
    name carries a run id nothing else will reuse.
    """
    path = layout.run_report(report.started_at, RunId(report.run_id))
    path.parent.mkdir(mode=RUNS_MODE, parents=True, exist_ok=True)
    write_model(path, report, mode=REPORT_MODE, code="HFVER007", error=IntegrityError)
    publish_verification_catalog(
        layout,
        verification_catalog(layout, outcome, mode=mode, report=layout.archive_relative(path)),
    )
    return path


def retained_keys(layout: ArchiveLayout) -> set[tuple[str, str, str]]:
    """Every `(type, id, commit_sha)` the archive retains, from the references alone.

    No model is loaded: a reference's *name* is what makes a SHA retained
    (`FS-11`), so the retained set can be read even when some of the references
    themselves cannot be. That matters here, because this set is what stops the
    verification catalog from accumulating entries about revisions the archive no
    longer holds.
    """
    return {
        (str(identity.type), identity.id, path.stem)
        for identity in published_repositories(layout)
        for path in (RepositoryLayout(archive=layout, identity=identity).refs / "revisions").glob(
            "*.json"
        )
        if _is_commit_sha(path.stem)
    }


def verification_catalog(
    layout: ArchiveLayout,
    outcome: VerificationOutcome,
    *,
    mode: Literal["new", "full", "revision"],
    report: PurePosixPath,
) -> VerificationCatalog:
    """Merge this run into the archive's verification headline (`docs/schemas.md` §5.2).

    A merge rather than a replacement, and the rule is the one §5.2 states: an
    entry is cleared only by a verification that re-read the same object, never
    by a run that simply did not look at it. So `verify --new` refreshes the
    revisions it covered and leaves the rest of the archive's history exactly as
    it was — which is what stops a narrow run from appearing to fix a problem it
    never examined.

    There is a third way an entry leaves, beyond §5.2's two: the revision is no
    longer retained. A pruned revision does not exist, and reporting the archive
    permanently degraded over content it no longer holds would be a health signal
    an operator could never clear.

    `last_full_verification` is replaced only by `--full`. A `--new` run measures
    a handful of objects, and letting its throughput stand as *the* measured rate
    would give the estimator a figure from the wrong workload.
    """
    previous = read_verification_catalog(layout)
    retained = retained_keys(layout)
    published = {(str(identity.type), identity.id) for identity in published_repositories(layout)}
    covered = {
        (str(revision.identity.type), revision.identity.id, revision.commit_sha)
        for revision in outcome.revisions_covered
        # A null-SHA outcome is the current reference, not a revision, and the
        # covered set is keyed by revision (`VER-009`).
        if revision.commit_sha is not None
    }
    return VerificationCatalog(
        generated_at=outcome.completed_at,
        last_full_verification=_last_full(previous, outcome, mode=mode, report=report),
        outstanding_failures=tuple(
            sorted(
                _outstanding(
                    previous,
                    outcome,
                    mode=mode,
                    published=published,
                    retained=retained,
                    covered=covered,
                ),
                key=lambda failure: failure.sort_key,
            )
        ),
        repositories=_repository_entries(previous, outcome, retained=retained, covered=covered),
    )


def _repository_entries(
    previous: VerificationCatalog | None,
    outcome: VerificationOutcome,
    *,
    retained: set[tuple[str, str, str]],
    covered: set[tuple[str, str, str]],
) -> tuple[RepositoryVerificationEntry, ...]:
    """Per-revision outcomes: this run's, over what the archive still retains."""
    held: dict[tuple[str, str], dict[str, VerificationRevisionEntry]] = {}
    for entry in previous.repositories if previous else ():
        for revision in entry.revisions:
            key = (entry.repository_type, entry.repository_id, revision.commit_sha)
            if key in retained and key not in covered:
                held.setdefault(key[:2], {})[revision.commit_sha] = revision
    for revision in outcome.revisions_covered:
        if revision.commit_sha is None:
            # The current reference would not parse (`VER-009`). Its finding is
            # in `outstanding_failures`; a per-revision outcome without a
            # revision would be meaningless here.
            continue
        key = (str(revision.identity.type), revision.identity.id)
        held.setdefault(key, {})[revision.commit_sha] = VerificationRevisionEntry(
            commit_sha=revision.commit_sha,
            outcome=revision.outcome,
            publication_id=revision.publication_id,
            verified_at=outcome.completed_at,
        )
    return tuple(
        sorted(
            (
                RepositoryVerificationEntry.model_validate(
                    {
                        "repository_id": repository_id,
                        "repository_type": repository_type,
                        "revisions": sorted(entries.values(), key=lambda item: item.commit_sha),
                    }
                )
                for (repository_type, repository_id), entries in held.items()
            ),
            key=lambda entry: (entry.repository_type, entry.repository_id),
        )
    )


def _outstanding(  # noqa: PLR0913 - the facts §5.2's clearing rules read, one argument each
    previous: VerificationCatalog | None,
    outcome: VerificationOutcome,
    *,
    mode: Literal["new", "full", "revision"],
    published: set[tuple[str, str]],
    retained: set[tuple[str, str, str]],
    covered: set[tuple[str, str, str]],
) -> list[OutstandingFailure]:
    """Carry forward what this run did not re-check, and record what it found.

    `first_seen_at` is preserved for a failure that was already outstanding, so
    an operator can tell a fault that appeared last night from one that has been
    reported for a quarter.
    """
    existing = previous.outstanding_failures if previous else ()
    seen = {failure.sort_key: failure.first_seen_at for failure in existing}
    kept = [
        failure
        for failure in existing
        if _still_outstanding(
            failure, mode=mode, published=published, retained=retained, covered=covered
        )
    ]
    return kept + [
        OutstandingFailure(
            commit_sha=finding.commit_sha,
            first_seen_at=seen.get(finding.sort_key, outcome.completed_at),
            kind=finding.kind,
            path=finding.path,
            publication_id=finding.publication_id,
            repository_id=finding.repository_id,
            repository_type=finding.repository_type,
        )
        for finding in outcome.findings
    ]


def _still_outstanding(
    failure: OutstandingFailure,
    *,
    mode: Literal["new", "full", "revision"],
    published: set[tuple[str, str]],
    retained: set[tuple[str, str, str]],
    covered: set[tuple[str, str, str]],
) -> bool:
    """Whether a run that produced no matching finding leaves this entry standing.

    A revision-keyed failure follows §5.2's rule: it stands while its revision is
    retained and this run did not re-read it.

    A failure with no `commit_sha` is the current reference itself (`VER-009`),
    and the revision rule cannot clear it — no retained key ever matches. The
    current-reference check runs only through `resolve_repository`, so only
    `--full` re-reads it today. Hence: a narrower run carries the entry forward
    unchanged, a `--full` run drops it — re-adding it with `first_seen_at`
    preserved when the reference is still unreadable — and a repository leaving
    `published/` takes it along. This rule must be revisited if a narrower mode
    ever grows the current-reference check, or a clean `--new` would clear a
    failure it never re-read.
    """
    if failure.commit_sha is None:
        return mode != "full" and (failure.repository_type, failure.repository_id) in published
    key = (failure.repository_type, failure.repository_id, failure.commit_sha)
    return key in retained and key not in covered


def _last_full(
    previous: VerificationCatalog | None,
    outcome: VerificationOutcome,
    *,
    mode: Literal["new", "full", "revision"],
    report: PurePosixPath,
) -> FullVerificationSummary | None:
    """This run's summary when it was a full one, otherwise the previous one."""
    if mode != "full":
        return previous.last_full_verification if previous else None
    return FullVerificationSummary(
        completed_at=outcome.completed_at,
        duration_seconds=outcome.duration_seconds,
        outcome=outcome.outcome,
        report=str(report),
        started_at=outcome.started_at,
        throughput_bytes_per_second=outcome.throughput_bytes_per_second,
        unique_bytes=outcome.bytes_read,
        unique_objects=outcome.objects_read,
    )
