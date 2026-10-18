"""Pure immutable command intent and CLI mode taxonomy (decision 120).

These requests carry no archive, credential, Hub or executor implementation.
Shared command services retain their compatibility exports for existing adapters.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Literal

from hfcache.errors import CodedError, ConfigurationError
from hfcache.identity import (
    CommitSha,
    RepositorySelector,
    parse_run_id,
    parse_selector,
    parse_transaction_id,
)

if TYPE_CHECKING:
    from pathlib import Path


UNPROVABLE_READ_ONLY: Final = (
    "directory_writability",
    "hardlink_capability",
    "atomic_directory_rename",
    "reference_replacement",
)
"""What `--read-only` cannot establish — every row the table marks as writing.

`docs/cli.md` §2 requires these to be reported as unproven rather than passed:
each one is a capability that can only be demonstrated by performing it, and a
mount that must not be touched is a mount on which they are unknown.
"""

READ_ONLY: Final = "--read-only: this capability can only be proven by exercising it"


@dataclass(frozen=True, slots=True)
class SelectionRequest:
    """Configured repository selection, preserved in configuration order."""

    selectors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "selectors", tuple(self.selectors))


ALL_CONFIGURED = SelectionRequest()


@dataclass(frozen=True, slots=True)
class DoctorRequest:
    """Whether diagnostic storage writes are authorized."""

    read_only: bool = False


@dataclass(frozen=True, slots=True)
class InitializationRequest:
    """Explicit initialization intent; configured target must be restated."""

    archive_root: Path
    archive_id: str | None = None
    confirm: bool = False
    inspect: bool = False


@dataclass(frozen=True, slots=True)
class MaintenanceRequest(SelectionRequest):
    """Explicit preview/apply mode and optional unmanaged purge scope."""

    dry_run: bool = False
    apply: bool = False
    all_unmanaged: bool = False

    def require_mode(self) -> None:
        """A preview never grants apply authority; neither mode is implicit."""
        if self.dry_run == self.apply:
            message = "exactly one of --dry-run and --apply is required"
            raise ConfigurationError.single(message, code="HFARG002")


@dataclass(frozen=True, slots=True)
class QuarantineRequest:
    """Only explicitly named completed redundant staging can be cleaned."""

    transaction_ids: tuple[str, ...] = ()
    dry_run: bool = False
    apply: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "transaction_ids", tuple(self.transaction_ids))

    def validate_scope(self) -> None:
        """Classify named-ID grammar before a CLI can contact the writer."""
        for identifier in self.transaction_ids:
            try:
                parse_transaction_id(identifier, code="HFARG001")
            except CodedError as error:
                raise ConfigurationError.single(str(error), code="HFARG001") from None


@dataclass(frozen=True, slots=True)
class RepairRequest:
    """One retained SHA and the operator's audit reason."""

    selector: str
    reason: str = "operator_requested"
    target: RepositorySelector = field(init=False, repr=False)
    commit_sha: CommitSha = field(init=False, repr=False)

    def __post_init__(self) -> None:
        parsed = parse_selector(self.selector)
        if parsed.commit_sha is None:
            message = (
                f"repair {self.selector!r} names no revision; it takes TYPE:ID@SHA with the "
                "full 40-character commit SHA, because a repair replaces one instance of one SHA"
            )
            raise ConfigurationError.single(message, code="HFARG001", location="TYPE:ID@SHA")
        object.__setattr__(self, "target", parsed)
        object.__setattr__(self, "commit_sha", parsed.commit_sha)


@dataclass(frozen=True, slots=True)
class VerificationRequest:
    """Verification scope, with exactly one selected mode."""

    new: bool = False
    full: bool = False
    revision: str | None = None
    estimate: bool = False
    run_id: str | None = None

    @property
    def command(self) -> str:
        """Name even an invalid invocation without accepting its options."""
        mode = _mode_option(
            new=self.new, full=self.full, revision=self.revision, estimate=self.estimate
        )
        return f"verify --{mode}"

    @property
    def mode(self) -> Literal["new", "full", "revision", "estimate"]:
        """Validate the existing CLI mode combinations with stable taxonomy."""
        return _verification_mode(
            new=self.new,
            full=self.full,
            revision=self.revision,
            estimate=self.estimate,
            run_id=self.run_id,
        )

    def validate_scope(self) -> None:
        """Prove CLI scope grammar before credentials or a submission are attempted."""
        if self.revision is not None:
            try:
                parsed = parse_selector(self.revision)
            except CodedError as error:
                raise ConfigurationError.single(
                    str(error), code="HFARG001", location="--revision"
                ) from None
            if parsed.commit_sha is None:
                message = "--revision requires TYPE:ID@SHA with the full 40-character commit SHA"
                raise ConfigurationError.single(message, code="HFARG001", location="--revision")
        if self.run_id is not None:
            try:
                parse_run_id(self.run_id, code="HFARG001")
            except CodedError as error:
                raise ConfigurationError.single(
                    str(error), code="HFARG001", location="--run-id"
                ) from None


def _chosen_modes(*, new: bool, full: bool, revision: str | None, estimate: bool) -> list[str]:
    """Which mode options this invocation named, in `docs/cli.md` §2's order."""
    return [
        name
        for name, given in (
            ("--new", new),
            ("--full", full),
            ("--revision", revision is not None),
            ("--estimate", estimate),
        )
        if given
    ]


def _mode_option(*, new: bool, full: bool, revision: str | None, estimate: bool) -> str:
    """The mode name for the `command` field, before the invocation is validated.

    A refusal still has to say which command was refused, and an invocation that
    named two modes or none is reported under the first mode it named or under
    `--new`; naming the command is not the same as accepting it.
    """
    chosen = _chosen_modes(new=new, full=full, revision=revision, estimate=estimate)
    return chosen[0].removeprefix("--") if chosen else "new"


def _verification_mode(
    *, new: bool, full: bool, revision: str | None, estimate: bool, run_id: str | None
) -> Literal["new", "full", "revision", "estimate"]:
    """Decide which mode was asked for, refusing none and refusing two.

    `docs/cli.md` §2: exactly one mode option is required. There is no default —
    the modes differ by orders of magnitude in what they read, and guessing which
    an operator meant would either skip most of the archive or saturate the NAS
    for an hour.
    """
    chosen = _chosen_modes(new=new, full=full, revision=revision, estimate=estimate)
    if len(chosen) > 1:
        message = (
            f"{' and '.join(chosen)} were given together; verify takes exactly one mode option, "
            f"because each names a different scope rather than a different amount of effort"
        )
        raise ConfigurationError.single(message, code="HFARG002", location="verify")
    if not chosen:
        message = (
            "verify requires exactly one mode option; --new checks the content one run "
            "introduced, --full every retained revision, --revision one of them, and "
            "--estimate none of them"
        )
        raise ConfigurationError.single(message, code="HFARG003", location="verify")
    if run_id is not None and not new:
        message = (
            f"--run-id names which run {chosen[0]} would check, and {chosen[0]} is not scoped to "
            f"a run; it is accepted only with --new"
        )
        raise ConfigurationError.single(message, code="HFARG002", location="--run-id")
    if full:
        return "full"
    if estimate:
        return "estimate"
    return "revision" if revision is not None else "new"
