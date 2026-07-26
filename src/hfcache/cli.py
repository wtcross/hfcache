"""Command-line interface for hfcache.

The command surface, global options, JSON envelope, and exit codes are specified
in `docs/cli.md`. Scheduled runs use exactly the same commands an operator types.
"""

import os
import platform
import socket
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Final, NoReturn

import typer

from hfcache import __version__
from hfcache.archive import initialize_archive, inspect_archive
from hfcache.config import ApplicationConfig, RepositoryConfig, load_config
from hfcache.credentials import resolve_token
from hfcache.errors import ConfigurationError, ExitCode, HfcacheError, Problem, SafetyError
from hfcache.hub import HubClient
from hfcache.identity import RepositoryIdentity, new_run_id, parse_selector
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
from hfcache.publication import projected_publication_bytes
from hfcache.recovery import apply_recovery, measure_health, plan_recovery
from hfcache.reporting import Envelope, EnvelopeProblem

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hfcache.archive import ArchiveInspection

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
) -> None:
    """Write the single JSON envelope defined by `docs/cli.md` §4 to stdout.

    Serialization goes through the same function durable artifacts use, so
    sorted keys, UTF-8, and the single trailing newline cannot differ between
    them. The envelope is written unindented: it is one machine-read line on a
    pipe, where a durable file is something an operator reads and diffs. Logs
    and progress go to stderr, so piping stdout is always safe.
    """
    outcome = "failed" if exit_code else ("success_with_warnings" if warnings else "success")
    envelope = Envelope(
        command=command,
        completed_at=utc_now(),
        data=data,
        errors=tuple(EnvelopeProblem.of(problem) for problem in errors),
        exit_code=exit_code,
        outcome=outcome,
        run_id=new_run_id(),
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
    payload: dict[str, Any] = {
        "application": __version__,
        "huggingface_hub": _dependency_version("huggingface-hub"),
        "python": platform.python_version(),
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

    entries = [
        {
            "enabled": repository.enabled,
            "managed": True,
            "repository_id": repository.id,
            "repository_type": repository.type,
            "requested_revision": repository.revision,
            "upstream_state": "unknown",
        }
        for repository in selected
    ]
    archive: dict[str, Any] = {
        "archive_id": config.storage.archive_id,
        "root": str(config.storage.archive_root),
    }
    # Health is reported when it can be measured and omitted when it cannot.
    # `status` answers even against an archive that is absent or unmounted
    # (`docs/cli.md` §2), so an unreachable root reports local configuration
    # truth rather than failing.
    layout = ArchiveLayout(root=config.storage.archive_root)
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
    return {
        "application_version": __version__,
        "archive_id": config.storage.archive_id,
        "config_fingerprint": config.fingerprint(),
        "hostname": socket.gethostname(),
        "huggingface_hub_version": _dependency_version("huggingface-hub"),
        # systemd sets INVOCATION_ID for every unit it starts, which is the one
        # signal that distinguishes a timer run from an operator at a terminal.
        "invocation_mode": "systemd" if os.environ.get("INVOCATION_ID") else "interactive",
        "python_version": platform.python_version(),
    }
