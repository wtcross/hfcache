"""Command-line interface for hfcache.

The command surface, global options, JSON envelope, and exit codes are specified
in `docs/cli.md`. Scheduled runs use exactly the same commands an operator types.
"""

import os
import socket
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Final, Literal, NoReturn

import typer

from hfcache.archive import initialize_archive, inspect_archive
from hfcache.config import ApplicationConfig, RepositoryConfig, load_config
from hfcache.credentials import resolve_token
from hfcache.errors import (
    ConfigurationError,
    ExitCode,
    HfcacheError,
    IntegrityError,
    Problem,
    SafetyError,
)
from hfcache.hub import HubClient, networking_disabled
from hfcache.identity import (
    REPOSITORY_TYPES,
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    new_run_id,
    parse_selector,
)
from hfcache.manifests import RevisionManifest
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.preflight import (
    READ_ONLY,
    UNPROVABLE_READ_ONLY,
    Check,
    guarded,
    hub_checks,
    order_checks,
    storage_checks,
)
from hfcache.publication import (
    projected_publication_bytes,
    published_repositories,
    read_reference,
    retained_references,
)
from hfcache.recovery import apply_recovery, measure_health, plan_recovery
from hfcache.reporting import Envelope, EnvelopeProblem, RunReport, RuntimeVersions
from hfcache.retention import apply_prune, plan_all
from hfcache.storage import read_model
from hfcache.sync import synchronize
from hfcache.verification import (
    FINDING_CODES,
    UNDETECTABLE,
    build_report,
    estimate_verification,
    require_retained,
    resolve_archive,
    resolve_run,
    verify_targets,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from hfcache.archive import ArchiveInspection
    from hfcache.models import PrunePlan, Reference
    from hfcache.reporting import VerificationReport
    from hfcache.verification import Resolved

__all__ = ["UNPROVABLE_READ_ONLY", "app"]

DEFAULT_CONFIG_PATH = Path("/etc/hfcache/config.toml")
"""Matches the systemd invocation in `docs/plan.md` §22.2."""

app = typer.Typer(
    name="hfcache",
    help=("Archive complete revisions of public Hugging Face repositories on long-term storage."),
    no_args_is_help=True,
    add_completion=False,
)


@dataclass(frozen=True, slots=True)
class GlobalOptions:
    """Options accepted before the command, per `docs/cli.md` §1."""

    config_path: Path
    json_output: bool
    verbose: int
    quiet: bool
    color: bool
    token_file: Path | None


def utc_now() -> str:
    """Return an RFC 3339 UTC timestamp in the durable-schema format.

    `docs/schemas.md` §1 requires microsecond precision and a literal `Z`.
    """
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _options(ctx: typer.Context) -> GlobalOptions:
    """Retrieve the global options attached by the callback."""
    if not isinstance(ctx.obj, GlobalOptions):  # pragma: no cover - defensive
        message = "global options were not initialised"
        raise TypeError(message)
    return ctx.obj


def emit_envelope(
    command: str,
    data: dict[str, Any],
    *,
    started_at: str,
    warnings: Sequence[Problem] = (),
    errors: Sequence[Problem] = (),
    exit_code: int = 0,
    run_id: str | None = None,
) -> None:
    """Write the single JSON envelope defined by `docs/cli.md` §4 to stdout.

    Serialization goes through the same function durable artifacts use, so
    sorted keys, UTF-8, and the single trailing newline cannot differ between
    them. The envelope is written unindented: it is one machine-read line on a
    pipe, where a durable file is something an operator reads and diffs. Logs
    and progress go to stderr, so piping stdout is always safe.

    `run_id` is passed by a command that wrote a durable report, because §4 says
    the envelope's run id *correlates it with that report* — minting a fresh one
    would give an operator two identifiers for one run and no way to join them.
    A command that writes no report has nothing to correlate with and gets a new
    id, which still ties the envelope to that invocation's log lines.
    """
    outcome = "failed" if exit_code else ("success_with_warnings" if warnings else "success")
    envelope = Envelope(
        command=command,
        completed_at=utc_now(),
        data=data,
        errors=tuple(EnvelopeProblem.of(problem) for problem in errors),
        exit_code=exit_code,
        outcome=outcome,
        run_id=run_id if run_id is not None else new_run_id(),
        started_at=started_at,
        warnings=tuple(EnvelopeProblem.of(problem) for problem in warnings),
    )
    sys.stdout.write(envelope.to_json(indent=None))


def _report_failure(
    ctx: typer.Context,
    command: str,
    started_at: str,
    error: HfcacheError,
    data: dict[str, Any] | None = None,
) -> NoReturn:
    """Render a failure and exit with its classification.

    The envelope is emitted on failure too (`docs/cli.md` §4), so automation
    never has to parse human text to learn what went wrong. In human mode the
    problems go to stderr, which is why `--quiet` can suppress everything else
    and still leave an operator with the reason.

    `data` is carried when the command determined something worth reporting
    before it refused — `archive init` describes the target it would not touch,
    so the same output answers both "why did it stop" and "what is there now".
    """
    if _options(ctx).json_output:
        emit_envelope(
            command,
            data or {},
            started_at=started_at,
            errors=error.problems,
            exit_code=int(error.exit_code),
        )
    else:
        for problem in error.problems:
            typer.echo(problem.as_line(), err=True)
    raise typer.Exit(int(error.exit_code))


def _echo_pairs(payload: dict[str, Any]) -> None:
    """Print a flat payload as aligned `key  value` lines."""
    width = max(len(key) for key in payload)
    for key in sorted(payload):
        typer.echo(f"{key.replace('_', ' '):<{width}}  {payload[key]}")


def _dependency_version(distribution: str) -> str:
    try:
        return package_version(distribution)
    except PackageNotFoundError:  # pragma: no cover - a broken installation
        return "unknown"


def _transfer_backend() -> str:
    """Report which Hub transfer path this installation will use.

    Reported by `version` because a deployment that silently lost the Xet
    backend would still work, only far more slowly, and the difference should be
    visible without running a download.
    """
    if find_spec("hf_xet") is None:
        return "http"
    return f"xet {_dependency_version('hf-xet')}"


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option("--config", metavar="PATH", help="Configuration file."),
    ] = DEFAULT_CONFIG_PATH,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the machine-readable envelope on stdout."),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Raise log detail. Repeatable."),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress progress and informational output."),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Force plain output."),
    ] = False,
    token_file: Annotated[
        Path | None,
        typer.Option(
            "--token-file",
            metavar="PATH",
            help="Read a Hub token from this file. Never logged.",
        ),
    ] = None,
) -> None:
    """Options accepted before the command."""
    ctx.obj = GlobalOptions(
        config_path=config,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
        # Colour is also suppressed when stdout is not a terminal, so journald
        # never receives escape sequences.
        color=not no_color and sys.stdout.isatty(),
        token_file=token_file,
    )


@app.command()
def version(ctx: typer.Context) -> None:
    """Show application and dependency versions.

    Reads no configuration and touches no archive, so it works on a deployment
    that is otherwise broken.
    """
    started_at = utc_now()
    versions = RuntimeVersions.measured()
    payload: dict[str, Any] = {
        "application": versions.application,
        "huggingface_hub": versions.huggingface_hub,
        "python": versions.python,
        "transfer_backend": _transfer_backend(),
    }
    if _options(ctx).json_output:
        emit_envelope("version", payload, started_at=started_at)
        return
    _echo_pairs(payload)


config_app = typer.Typer(
    name="config",
    help="Inspect and validate configuration.",
    no_args_is_help=True,
)
app.add_typer(config_app)


@config_app.command("validate")
def config_validate(ctx: typer.Context) -> None:
    """Parse and fully validate configuration, touching nothing.

    Runs exactly the validation every mutating command runs — the same loader,
    the same credential resolution — and takes no lock, checks no mount, and
    makes no network request (`docs/cli.md` §2). That is what makes it safe to
    run against production configuration from a shell at any time, and it is why
    a green `config validate` means a scheduled run will get as far as the mount
    check rather than failing on a typo hours later.
    """
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        token = resolve_token(config.hub, token_file=options.token_file)
    except HfcacheError as error:
        _report_failure(ctx, "config validate", started_at, error)

    payload: dict[str, Any] = {
        "config_fingerprint": config.fingerprint(),
        "enabled_repositories": len(config.enabled_repositories),
        "repositories": len(config.repositories),
        # The source, never the value (`docs/security.md` T-07). An operator
        # checking a deployment needs to know whether the credential resolved
        # and from where; learning that only from a sync hours later is worse.
        "token_source": token.source.value,
    }
    if options.json_output:
        emit_envelope("config validate", payload, started_at=started_at)
        return
    if not options.quiet:
        _echo_pairs(payload)


# --------------------------------------------------------------------------- #
# archive init (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #

archive_app = typer.Typer(
    name="archive",
    help="Create and inspect the archive itself.",
    no_args_is_help=True,
)
app.add_typer(archive_app)


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


@archive_app.command("init")
def archive_init(
    ctx: typer.Context,
    archive_root: Annotated[
        Path,
        typer.Option("--archive-root", metavar="PATH", help="Archive root; must match config."),
    ],
    archive_id: Annotated[
        str | None,
        typer.Option("--archive-id", metavar="UUID", help="Restate the provisioned archive UUID."),
    ] = None,
    confirm: Annotated[
        bool,
        typer.Option("--confirm", help="Perform the initialization. Required for mutation."),
    ] = False,
    inspect: Annotated[
        bool,
        typer.Option("--inspect", help="Describe the target without touching it."),
    ] = False,
) -> None:
    """Create the archive layout and its sentinel, exactly once.

    This is the only command that creates the archive (`FS-21`), it is never
    reached from a timer or a recovery path, and it refuses anything it did not
    create rather than making room for itself. Without `--confirm` it describes
    what it would do and exits `10`.
    """
    started_at = utc_now()
    options = _options(ctx)
    command = "archive init"
    try:
        config = load_config(options.config_path)
        _check_init_options(
            config,
            archive_root=archive_root,
            archive_id=archive_id,
            confirm=confirm,
            inspect=inspect,
        )
        layout = ArchiveLayout(root=config.storage.archive_root)
        inspection = inspect_archive(layout, archive_id=config.storage.archive_id)
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)

    found = inspection.as_payload()
    if inspection.problems:
        _report_failure(ctx, command, started_at, SafetyError(inspection.problems), found)
    if inspect:
        _emit(ctx, command, found, started_at=started_at, lines=_inspection_lines(inspection))
        return
    if not inspection.initializable:
        message = (
            f"archive {layout.root} is already initialized; initialization happens once, "
            f"because a second sentinel would give an existing archive a new identity"
        )
        error = SafetyError.single(message, code="HFMNT014", location=str(layout.root))
        _report_failure(ctx, command, started_at, error, found)
    if not confirm:
        message = (
            f"--confirm is required to initialize {layout.root}; nothing was changed. The "
            f"reported state is what initialization would act on"
        )
        error = ConfigurationError.single(message, code="HFARG003", location=str(layout.root))
        _report_failure(ctx, command, started_at, error, found)

    try:
        result = initialize_archive(layout, archive_id=config.storage.archive_id)
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error, found)
    _emit(
        ctx,
        command,
        result.as_payload(),
        started_at=started_at,
        lines={
            "archive root": str(result.layout.root),
            "archive id": result.sentinel.archive_id,
            "created": f"{len(result.created_directories)} directories",
            "adopted published": "yes" if result.adopted_published else "no",
            "sentinel": str(result.layout.sentinel),
        },
    )


def _inspection_lines(inspection: ArchiveInspection) -> dict[str, str]:
    """Summarize an inspection for an operator reading a terminal."""
    entry = inspection.mount.entry
    return {
        "archive root": str(inspection.layout.root),
        "state": inspection.state,
        "filesystem": f"{entry.filesystem_type} from {entry.source}" if entry else "not a mount",
        "initializable": "yes" if inspection.initializable else "no",
        "existing directories": str(len(inspection.existing_directories)),
        "missing directories": str(len(inspection.missing_directories)),
        "unknown entries": str(inspection.unknown_entry_count),
        "adopted published": "yes" if inspection.adopted_published else "no",
    }


def _emit(
    ctx: typer.Context,
    command: str,
    payload: dict[str, Any],
    *,
    started_at: str,
    lines: dict[str, str],
) -> None:
    """Write either the envelope or the human summary, never both."""
    options = _options(ctx)
    if options.json_output:
        emit_envelope(command, payload, started_at=started_at)
        return
    if not options.quiet:
        _echo_pairs(lines)


# --------------------------------------------------------------------------- #
# Selectors (`docs/cli.md` §1.1)
# --------------------------------------------------------------------------- #

SelectorArgument = Annotated[
    list[str] | None,
    typer.Argument(metavar="[TYPE:ID ...]", help="Restrict the command to these repositories."),
]


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


# --------------------------------------------------------------------------- #
# doctor
# --------------------------------------------------------------------------- #


@app.command()
def doctor(
    ctx: typer.Context,
    read_only: Annotated[
        bool,
        typer.Option("--read-only", help="Run only the checks that mutate nothing."),
    ] = False,
) -> None:
    """Prove the deployment can do what a scheduled run will ask of it.

    Every check is reported, in the normative order of the `docs/cli.md` §2
    table, so the output is a record of what was proven rather than of where the
    command stopped. The checks themselves are `hfcache.preflight`'s, which is
    the same runner a mutating command's hard gate uses — the report an operator
    reads and the preflight a scheduled run performs cannot describe different
    things (plan §19).
    """
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        token = resolve_token(config.hub, token_file=options.token_file)
    except HfcacheError as error:
        _report_failure(ctx, "doctor", started_at, error)

    layout = ArchiveLayout(root=config.storage.archive_root)
    checks = [
        Check.passed(
            "configuration",
            f"{options.config_path} is valid; fingerprint {config.fingerprint()[:12]}",
        ),
        *storage_checks(layout, storage=config.storage, read_only=read_only),
        Check.passed("credential", token.describe()),
        Check.passed("hub_endpoint", f"{config.hub.endpoint} is a well-formed https endpoint"),
        *hub_checks(config.hub, HubClient.of(token, endpoint=config.hub.endpoint)),
    ]
    if read_only:
        # Whatever the runner did not already report as unprovable. As the
        # packages behind those capabilities land they leave this list, rather
        # than being stated in two places that could disagree.
        probed = {check.name for check in checks}
        checks.extend(
            Check.skipped(name, READ_ONLY) for name in UNPROVABLE_READ_ONLY if name not in probed
        )

    ordered = order_checks(checks)
    problems = [problem for check in ordered for problem in check.problems]
    warnings = [warning for check in ordered for warning in check.warnings]
    failed = any(check.outcome == "fail" for check in ordered)
    exit_code = int(ExitCode.SAFETY) if failed else int(ExitCode.SUCCESS)

    payload: dict[str, Any] = {"checks": [check.as_entry() for check in ordered]}
    if options.json_output:
        emit_envelope(
            "doctor",
            payload,
            started_at=started_at,
            warnings=warnings,
            errors=problems,
            exit_code=exit_code,
        )
    elif not options.quiet:
        # The table is the report: a failing row already carries its problem's
        # message as its detail, so repeating the problems on stderr would say
        # the same thing twice.
        width = max(len(check.name) for check in ordered)
        for check in ordered:
            typer.echo(f"{check.outcome:<7}  {check.name:<{width}}  {check.detail}")
    if failed:
        raise typer.Exit(exit_code)


# --------------------------------------------------------------------------- #
# plan and status
# --------------------------------------------------------------------------- #


@app.command()
def plan(ctx: typer.Context, selectors: SelectorArgument = None) -> None:
    """Report the work a sync would do. Mutates nothing and takes no lock.

    This is the command run before enabling a large repository, and its output
    is what the dataset quota is sized from (`docs/cli.md` §2). It resolves each
    enabled repository's configured reference to a full commit SHA, which is the
    same resolution a sync performs — so a `plan` that answers cleanly is
    evidence the sync will get as far as downloading.

    One repository failing does not abandon the rest: each is reported with the
    upstream state that was observed, and the run exits `30` if any failed. An
    operator with ten repositories and one typo should learn about the typo and
    still see the other nine.
    """
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        token = resolve_token(config.hub, token_file=options.token_file)
        selected = _select(config, selectors)
    except HfcacheError as error:
        _report_failure(ctx, "plan", started_at, error)

    client = HubClient.of(token, endpoint=config.hub.endpoint)
    cache_dir = ArchiveLayout(root=config.storage.archive_root).hub_cache
    entries: list[dict[str, Any]] = []
    problems: list[Problem] = []
    for repository in selected:
        if not repository.enabled:
            continue
        entry, failure = _planned(client, repository, config, cache_dir=cache_dir)
        entries.append(entry)
        if failure is not None:
            problems.append(failure)

    exit_code = int(ExitCode.SYNC) if problems else int(ExitCode.SUCCESS)
    payload: dict[str, Any] = {"repositories": entries}
    if options.json_output:
        emit_envelope("plan", payload, started_at=started_at, errors=problems, exit_code=exit_code)
    elif not options.quiet:
        for entry in entries:
            typer.echo(_plan_line(entry))
    if problems:
        raise typer.Exit(exit_code)


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


def _plan_line(entry: dict[str, Any]) -> str:
    """One repository's row of human-readable `plan` output.

    An entry whose resolution failed has no sizes to show, so it reports the
    upstream state in the place the SHA would have been — which is the answer an
    operator running `plan` against a typo wants first.
    """
    selector = f"{entry['repository_type']}:{entry['repository_id']}@{entry['requested_revision']}"
    if entry["resolved_commit_sha"] is None:
        return f"{selector}  {entry['upstream_state']}"
    line = f"{selector}  {entry['resolved_commit_sha']}"
    if entry["file_count"] is None:
        return line
    line = f"{line}  {entry['file_count']} files, {_bytes(entry['logical_bytes'])}"
    if entry["estimated_new_bytes"] is not None:
        line = f"{line}, {_bytes(entry['estimated_new_bytes'])} new"
    if entry["projected_publication_bytes"]:
        line = f"{line}, {_bytes(entry['projected_publication_bytes'])} to publish"
    return line


def _bytes(value: int) -> str:
    """Render a byte count at a scale an operator can read.

    Not `preflight`'s GiB rendering, which is right for a dataset reserve and
    useless for a repository: the two small test repositories would both show as
    `0.0 GiB`, and `plan` is the command that has to tell them apart.
    """
    for unit, threshold in (("GiB", 1024**3), ("MiB", 1024**2), ("KiB", 1024)):
        if value >= threshold:
            return f"{value / threshold:.1f} {unit}"
    return f"{value} B"


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


@app.command()
def status(ctx: typer.Context, selectors: SelectorArgument = None) -> None:
    """Report local truth about the archive.

    Never fails merely because the Hub is unreachable (`docs/cli.md` §2): it
    reports what is known locally and marks upstream state `unknown`. This is the
    command an operator runs first, so it answers even when everything else is
    broken.
    """
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        selected = _select(config, selectors)
    except HfcacheError as error:
        _report_failure(ctx, "status", started_at, error)

    layout = ArchiveLayout(root=config.storage.archive_root)
    last_run = _last_run_statuses(layout)
    entries = [_status_entry(layout, repository, last_run) for repository in selected]
    archive: dict[str, Any] = {
        "archive_id": config.storage.archive_id,
        "root": str(config.storage.archive_root),
    }
    # Health is reported when it can be measured and omitted when it cannot.
    # `status` answers even against an archive that is absent or unmounted
    # (`docs/cli.md` §2), so an unreachable root reports local configuration
    # truth rather than failing.
    warnings: list[Problem] = []
    try:
        health = measure_health(
            layout,
            config.storage,
            stale_staging_age_hours=config.sync.stale_staging_age_hours,
        )
    except HfcacheError:
        archive["reachable"] = False
    else:
        archive["reachable"] = True
        archive |= health.as_payload()
        warnings.extend(health.reconciliation.warnings)

    payload: dict[str, Any] = {"archive": archive, "repositories": entries}
    if options.json_output:
        emit_envelope("status", payload, started_at=started_at, warnings=warnings)
        return
    if not options.quiet:
        for entry in entries:
            state = "enabled" if entry["enabled"] else "disabled"
            typer.echo(f"{entry['repository_type']}:{entry['repository_id']}  {state}")
        for warning in warnings:
            typer.echo(warning.as_line(), err=True)


# --------------------------------------------------------------------------- #
# sync (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@app.command()
def sync(ctx: typer.Context, selectors: SelectorArgument = None) -> None:
    """Synchronize configured repositories (plan §13.1).

    The scheduled command, and the only one that downloads. It runs the §13.1
    sequence in order: load configuration, take the exclusive lock, prove the
    §19 storage requirements, then process repositories in deterministic
    configuration order, rebuild the derived catalog, and write a durable run
    report.

    The lock and the preflight are held for the whole run rather than checked
    per repository, which is what makes them mean anything: proving the archive
    sound and then letting another command mutate it throughout would prove
    nothing.
    """
    started_at = datetime.now(UTC)
    stamp = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        token = resolve_token(config.hub, token_file=options.token_file)
        selected = _select(config, selectors)
    except HfcacheError as error:
        _report_failure(ctx, "sync", stamp, error)

    client = HubClient.of(token, endpoint=config.hub.endpoint)
    layout = ArchiveLayout(root=config.storage.archive_root)
    try:
        with guarded(
            layout,
            storage=config.storage,
            command="sync",
            lock_wait_seconds=config.sync.lock_wait_seconds,
        ):
            run_id = new_run_id()
            outcome = synchronize(
                client,
                layout,
                config,
                selected=selected,
                envelope=_run_envelope(config),
                run_id=run_id,
                started_at=started_at,
            )
    except HfcacheError as error:
        _report_failure(ctx, "sync", stamp, error)

    payload = outcome.report.model_dump(mode="json")
    payload["report"] = str(layout.archive_relative(outcome.report_path))
    # The envelope's arrays are rebuilt from the durable report rather than
    # collected separately, so the two cannot describe different runs. Each entry
    # names the repository it belongs to, which is what an operator with ten
    # configured repositories and one failure needs first.
    problems = [
        Problem(
            code=code,
            message=f"{result.repository_type}:{result.repository_id} failed",
            repository=f"{result.repository_type}:{result.repository_id}",
        )
        for result in outcome.report.repositories
        for code in result.errors
    ]
    warnings = [
        Problem(
            code=code,
            message=f"{result.repository_type}:{result.repository_id} warned",
            repository=f"{result.repository_type}:{result.repository_id}",
        )
        for result in outcome.report.repositories
        for code in result.warnings
    ]
    if options.json_output:
        emit_envelope(
            "sync",
            payload,
            started_at=stamp,
            warnings=warnings,
            errors=problems,
            exit_code=int(outcome.exit_code),
            run_id=run_id,
        )
    elif not options.quiet:
        for result in outcome.report.repositories:
            typer.echo(
                f"{result.repository_type}:{result.repository_id}  {result.status}"
                f"{'  ' + result.resolved_commit_sha if result.resolved_commit_sha else ''}"
            )
        for problem in problems:
            typer.echo(problem.as_line(), err=True)
    if outcome.exit_code != ExitCode.SUCCESS:
        raise typer.Exit(int(outcome.exit_code))


def _status_entry(
    layout: ArchiveLayout, repository: RepositoryConfig, last_run: Mapping[str, str]
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
    identity = RepositoryIdentity.from_config(repository)
    entry: dict[str, Any] = {
        "current_commit_sha": None,
        "current_publication_generation": None,
        "enabled": repository.enabled,
        "last_run_status": last_run.get(identity.selector),
        "managed": True,
        "repository_id": repository.id,
        "repository_type": repository.type,
        "requested_revision": repository.revision,
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
        entry["verification_state"] = "verified"
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


# --------------------------------------------------------------------------- #
# list (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@app.command(name="list")
def list_repositories(
    ctx: typer.Context,
    selectors: SelectorArgument = None,
    repository_type: Annotated[
        str | None,
        typer.Option("--type", metavar="model|dataset", help="Restrict to one repository type."),
    ] = None,
    revisions: Annotated[
        bool,
        typer.Option("--revisions", help="Include every retained revision."),
    ] = False,
) -> None:
    """List archived repositories and revisions.

    Reads only manifests and references (`docs/cli.md` §2), never the catalog.
    That is the point of the command: the catalog is derived and can be missing
    or corrupt (`FS-16`), and an operator taking inventory during an incident is
    exactly the person who cannot rely on it. Rebuilding the same view from the
    authoritative artifacts costs a directory walk and answers regardless.

    Takes no lock and mutates nothing, so it is safe to run during a sync.
    """
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        wanted = {
            RepositoryIdentity.from_config(repository).selector
            for repository in _select(config, selectors)
        }
        if repository_type is not None and repository_type not in REPOSITORY_TYPES:
            message = (
                f"--type must be one of {', '.join(sorted(REPOSITORY_TYPES))}; "
                f"{repository_type!r} is neither"
            )
            raise ConfigurationError.single(message, code="HFARG002", location="--type")
    except HfcacheError as error:
        _report_failure(ctx, "list", started_at, error)

    layout = ArchiveLayout(root=config.storage.archive_root)
    configured = {
        RepositoryIdentity.from_config(repository).selector: repository
        for repository in config.repositories
    }
    entries: list[dict[str, Any]] = []
    for identity in published_repositories(layout):
        if repository_type is not None and identity.type != repository_type:
            continue
        # Selectors restrict the *configured* set, so a selector never hides an
        # unmanaged repository the operator did not ask about by name.
        if selectors and identity.selector not in wanted:
            continue
        entries.append(_listed(layout, identity, configured.get(identity.selector), revisions))

    _emit(
        ctx,
        "list",
        {"repositories": entries},
        started_at=started_at,
        lines={
            f"{entry['repository_type']}:{entry['repository_id']}": (
                f"{entry['retained_revisions']} revisions"
                + (
                    f"  current {entry['current_commit_sha']}"
                    if entry["current_commit_sha"]
                    else ""
                )
            )
            for entry in entries
        },
    )


def _listed(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    configured: RepositoryConfig | None,
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
        entry["revisions"] = [_listed_revision(repository, reference) for reference in held]
    return entry


def _listed_revision(repository: RepositoryLayout, reference: Reference) -> dict[str, Any]:
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
        "verification_state": "verified",
    }


# --------------------------------------------------------------------------- #
# verify (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@app.command()
def verify(
    ctx: typer.Context,
    new: Annotated[
        bool,
        typer.Option("--new", help="Verify the content one run introduced."),
    ] = False,
    full: Annotated[
        bool,
        typer.Option("--full", help="Verify every retained revision. The quarterly job."),
    ] = False,
    revision: Annotated[
        str | None,
        typer.Option("--revision", metavar="TYPE:ID@SHA", help="Verify one retained revision."),
    ] = None,
    estimate: Annotated[
        bool,
        typer.Option("--estimate", help="Report what a full verification would cost. No hashing."),
    ] = False,
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", metavar="ID", help="Which run --new checks. Default: the newest."),
    ] = None,
) -> None:
    """Re-read published content and compare it with its manifest (plan §16).

    Exits `0` on a clean result and `40` on any integrity finding. A finding
    never rewrites a manifest, prunes a revision, or re-downloads over the
    evidence (`docs/cli.md` §2, `AD-13`): it is recorded, reported, and left for
    an operator to act on with `repair`.

    `--new` covers exactly the content one run introduced, which is what makes it
    cheap enough to run after every sync. It resolves through the archive's
    current references rather than through the publication ids the run recorded,
    so a revision a later prune rotated out is not verified and a revision a
    later repair replaced is verified in its replacement.

    `--full` covers every retained revision of every repository the archive
    holds, including repositories no longer in configuration (`AD-06`) — a
    quarterly job that skipped those would leave exactly the content nothing else
    touches unchecked. It takes the exclusive lock, which is what makes it
    mutually exclusive with sync, prune, and repair, and runs with Hub networking
    disabled because it re-reads what the archive already has.

    `--revision TYPE:ID@SHA` checks one retained revision, which is what an
    operator reaches for after a `--full` reported a finding and again after a
    `repair` claims to have fixed it. The repository need not be in
    configuration: an unmanaged repository's data is still the archive's (`AD-06`)
    and is still worth checking.

    `--estimate` hashes nothing and takes no lock. It reports what `--full`
    would read, so that scheduling it against a NAS maintenance window is a
    decision made from a measurement rather than from a guess (plan §16.4).
    """
    started_at = datetime.now(UTC)
    stamp = utc_now()
    options = _options(ctx)
    command = f"verify --{_mode_option(new=new, full=full, revision=revision, estimate=estimate)}"
    try:
        mode = _verification_mode(
            new=new, full=full, revision=revision, estimate=estimate, run_id=run_id
        )
        config = load_config(options.config_path)
    except HfcacheError as error:
        _report_failure(ctx, command, stamp, error)

    layout = ArchiveLayout(root=config.storage.archive_root)
    if mode == "estimate":
        _emit_estimate(ctx, command, layout, started_at=stamp)
        return

    try:
        if mode == "full":
            # The lock first, then the §19 gate, then the work — the same order
            # every mutating command uses, because a verification that wrote its
            # report while a sync republished underneath it would be describing
            # an archive that no longer exists. Networking is off for the whole
            # of it (`docs/cli.md` §2).
            with (
                guarded(
                    layout,
                    storage=config.storage,
                    command=command,
                    lock_wait_seconds=config.verification.lock_wait_seconds,
                ),
                networking_disabled(),
            ):
                outcome = verify_targets(resolve_archive(layout), started_at=started_at)
        elif mode == "revision":
            outcome = verify_targets(
                (_named_revision(layout, str(revision)),), started_at=started_at
            )
        else:
            outcome = verify_targets(
                resolve_run(layout, _run_to_verify(layout, run_id)), started_at=started_at
            )
    except HfcacheError as error:
        _report_failure(ctx, command, stamp, error)

    report = build_report(
        outcome,
        envelope=_run_envelope(config),
        command=command,
        mode=mode,
        run_id=new_run_id(),
    )
    _emit_verification(ctx, command, report, started_at=stamp)


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


def _emit_estimate(
    ctx: typer.Context, command: str, layout: ArchiveLayout, *, started_at: str
) -> None:
    """Report what `--full` would cost, having hashed nothing (plan §16.4).

    Always exit `0`. Nothing was read, so nothing can have been found wrong, and
    an estimator that could report `40` would make an operator's scheduling
    question indistinguishable from an integrity answer.
    """
    estimate = estimate_verification(layout)
    payload = estimate.as_payload()
    duration = estimate.estimated_duration_seconds
    _emit(
        ctx,
        command,
        payload,
        started_at=started_at,
        lines={
            "repositories": str(estimate.repositories),
            "revisions": str(estimate.revisions),
            "unique objects": str(estimate.unique_objects),
            "unique bytes": _bytes(estimate.unique_bytes),
            "estimated duration": (
                f"{duration:.0f}s" if duration is not None else "unknown — never measured"
            ),
            "storage maintenance": UNDETECTABLE,
        },
    )


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


def _emit_verification(
    ctx: typer.Context, command: str, report: VerificationReport, *, started_at: str
) -> None:
    """Render a verification report and exit with its classification.

    The envelope's `errors` array is grouped by `(kind, repository)` rather than
    listing one entry per finding. A damaged archive can produce thousands, and
    an array that long is not something an operator or a log pipeline reads —
    the complete finding set is in `data`, which is the report body itself.
    """
    options = _options(ctx)
    problems = _finding_problems(report)
    payload = report.model_dump(mode="json")
    if options.json_output:
        emit_envelope(
            command,
            payload,
            started_at=started_at,
            errors=problems,
            exit_code=report.exit_code,
            run_id=report.run_id,
        )
    elif not options.quiet:
        _echo_pairs(
            {
                "outcome": report.verification_outcome,
                "repositories": str(report.scope.repositories),
                "revisions": str(report.scope.revisions),
                "objects read": str(report.scope.unique_objects_read),
                "bytes read": _bytes(report.scope.unique_bytes_read),
                "findings": str(len(report.findings)),
            }
        )
        for problem in problems:
            typer.echo(problem.as_line(), err=True)
    if report.exit_code != ExitCode.SUCCESS:
        raise typer.Exit(report.exit_code)


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


# --------------------------------------------------------------------------- #
# prune (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@app.command()
def prune(
    ctx: typer.Context,
    selectors: SelectorArgument = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the exact plan and mutate nothing."),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Execute a validated plan."),
    ] = False,
) -> None:
    """Inspect or complete retention cleanup (plan §15.2).

    Retention normally runs inside `sync`; this command exists to inspect the
    plan before it runs and to complete retention an earlier failure deferred
    (`docs/cli.md` §2).

    `--dry-run` reads only and takes no lock: it reports the plan `--apply`
    would execute, built from the same references and manifests the prune itself
    reads, so what an operator reviewed is what runs.

    `--apply` mutates, so it takes the exclusive lock and passes the same §19
    preflight as any other mutating command, and plans *inside* them — a plan
    made before the lock could be stale by the time it ran.
    """
    started_at = utc_now()
    options = _options(ctx)
    command = f"prune {'--apply' if apply else '--dry-run'}"
    try:
        if dry_run == apply:
            message = (
                "exactly one of --dry-run and --apply is required: one describes what would "
                "happen and the other performs it, and neither is a safe default"
            )
            raise ConfigurationError.single(message, code="HFARG002")
        config = load_config(options.config_path)
        wanted = {
            RepositoryIdentity.from_config(repository).selector
            for repository in _select(config, selectors)
        }
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)

    layout = ArchiveLayout(root=config.storage.archive_root)
    maximum = config.storage.maximum_revisions
    try:
        if apply:
            with guarded(
                layout,
                storage=config.storage,
                command=command,
                lock_wait_seconds=config.sync.lock_wait_seconds,
            ):
                plans = _plans(layout, wanted, maximum=maximum)
                # One run id for the whole invocation, so every prune journal
                # this command opens correlates with the same envelope and with
                # each other.
                envelope = _run_envelope(config) | {"run_id": new_run_id()}
                applied = [apply_prune(layout, plan, envelope=envelope) for plan in plans]
        else:
            plans = _plans(layout, wanted, maximum=maximum)
            applied = []
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)

    payload: dict[str, Any] = {
        "plans": [plan.model_dump(mode="json") for plan in plans],
        "applied": [record.model_dump(mode="json") for record in applied],
    }
    _emit(
        ctx,
        command,
        payload,
        started_at=started_at,
        lines={
            f"{plan.repository_type}:{plan.repository_id}": (
                f"prune generation {plan.selected.publication_generation} "
                f"({plan.selected.commit_sha})"
            )
            for plan in plans
        }
        or {"retention": "nothing to prune"},
    )


def _plans(layout: ArchiveLayout, wanted: set[str], *, maximum: int) -> tuple[PrunePlan, ...]:
    """Every prune the selected repositories need, in repository order."""
    identities = [
        identity for identity in published_repositories(layout) if identity.selector in wanted
    ]
    return plan_all(layout, identities, maximum=maximum, generated_at=datetime.now(UTC))


# --------------------------------------------------------------------------- #
# recover (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@app.command()
def recover(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Describe the plan and mutate nothing."),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Execute a fully validated plan. Idempotent."),
    ] = False,
) -> None:
    """Reconcile unfinished transaction journals (plan §18).

    Roll-forward oriented: it never replaces an expected digest, chooses a
    revision by modification time, or removes unknown data (`AD-16`). A state it
    may not resolve on its own is reported and exits `20` rather than guessed at,
    because a state two valid executions could both have produced has no single
    correct resolution.

    `--dry-run` reads only. `--apply` takes the same exclusive lock and runs the
    same storage preflight every mutating command does, because it is one.
    """
    started_at = datetime.now(UTC)
    stamp = utc_now()
    options = _options(ctx)
    command = f"recover {'--apply' if apply else '--dry-run'}"
    try:
        if dry_run == apply:
            message = (
                "exactly one of --dry-run and --apply is required: one describes what would "
                "happen and the other performs it, and neither is a safe default"
            )
            raise ConfigurationError.single(message, code="HFARG002")
        config = load_config(options.config_path)
    except HfcacheError as error:
        _report_failure(ctx, command, stamp, error)

    layout = ArchiveLayout(root=config.storage.archive_root)
    stale_hours = config.sync.stale_staging_age_hours
    payload: dict[str, Any] = {}
    try:
        if apply:
            # `--apply` mutates, so it takes the same lock and passes the same
            # §19 preflight as any other mutating command, and plans *inside*
            # them — a plan made before the lock could be stale by the time it
            # ran.
            with guarded(
                layout,
                storage=config.storage,
                command=command,
                lock_wait_seconds=config.sync.lock_wait_seconds,
            ):
                plan = plan_recovery(layout, stale_staging_age_hours=stale_hours)
                payload = plan.as_payload()
                if not plan.blocked:
                    report, applied = apply_recovery(
                        layout, plan, envelope=_run_envelope(config), started_at=started_at
                    )
                    payload |= {
                        "applied": len(applied),
                        "report": str(layout.archive_relative(report)),
                    }
        else:
            plan = plan_recovery(layout, stale_staging_age_hours=stale_hours)
            payload = plan.as_payload()
    except HfcacheError as error:
        _report_failure(ctx, command, stamp, error, payload)

    if plan.blocked:
        _report_failure(ctx, command, stamp, SafetyError(list(plan.problems)), payload)
    _emit(
        ctx,
        command,
        payload,
        started_at=stamp,
        lines={
            "actionable": str(payload["actionable"]),
            "blocked": str(payload["blocked"]),
            "applied": str(payload.get("applied", "-")),
        },
    )


def _run_envelope(config: ApplicationConfig) -> dict[str, Any]:
    """The provenance fields every durable report carries (`docs/schemas.md` §6)."""
    versions = RuntimeVersions.measured()
    return {
        "application_version": versions.application,
        "archive_id": config.storage.archive_id,
        "config_fingerprint": config.fingerprint(),
        "hostname": socket.gethostname(),
        "huggingface_hub_version": versions.huggingface_hub,
        # systemd sets INVOCATION_ID for every unit it starts, which is the one
        # signal that distinguishes a timer run from an operator at a terminal.
        "invocation_mode": "systemd" if os.environ.get("INVOCATION_ID") else "interactive",
        "python_version": versions.python,
    }
