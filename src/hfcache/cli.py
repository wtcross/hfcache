"""Command-line interface for hfcache.

The command surface, global options, JSON envelope, and exit codes are specified
in `docs/cli.md`. Scheduled runs use exactly the same commands an operator types.
"""

import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Final, Literal, NoReturn

import typer

from hfcache import __version__
from hfcache.config import ApplicationConfig, RepositoryConfig, load_config
from hfcache.credentials import resolve_token
from hfcache.errors import ConfigurationError, HfcacheError, Problem
from hfcache.identity import new_run_id, parse_selector
from hfcache.reporting import Envelope, EnvelopeProblem

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["app"]

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
    ctx: typer.Context, command: str, started_at: str, error: HfcacheError
) -> NoReturn:
    """Render a failure and exit with its classification.

    The envelope is emitted on failure too (`docs/cli.md` §4), so automation
    never has to parse human text to learn what went wrong. In human mode the
    problems go to stderr, which is why `--quiet` can suppress everything else
    and still leave an operator with the reason.
    """
    if _options(ctx).json_output:
        emit_envelope(
            command,
            {},
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


@dataclass(frozen=True, slots=True)
class Check:
    """One `doctor` probe and what it proved (`docs/cli.md` §4.1)."""

    name: str
    outcome: Literal["pass", "fail", "skipped"]
    detail: str

    def as_entry(self) -> dict[str, str]:
        """Render in the documented `checks[]` shape."""
        return {"detail": self.detail, "name": self.name, "outcome": self.outcome}


UNPROVABLE_READ_ONLY: Final = (
    "hardlink_capability",
    "atomic_directory_rename",
    "reference_replacement",
)
"""What `--read-only` cannot establish.

`docs/cli.md` §2 requires these to be reported as unproven rather than passed:
each one is a capability that can only be demonstrated by performing it, and a
mount that must not be touched is a mount on which they are unknown.
"""


@app.command()
def doctor(
    ctx: typer.Context,
    read_only: Annotated[
        bool,
        typer.Option("--read-only", help="Run only the checks that mutate nothing."),
    ] = False,
) -> None:
    """Prove the deployment can do what a scheduled run will ask of it.

    Checks run in a fixed order and every one is reported, so the output is a
    record of what was proven rather than of where the command stopped.
    """
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        token = resolve_token(config.hub, token_file=options.token_file)
    except HfcacheError as error:
        _report_failure(ctx, "doctor", started_at, error)

    checks = [
        Check(
            name="configuration",
            outcome="pass",
            detail=f"{options.config_path} is valid; fingerprint {config.fingerprint()[:12]}",
        ),
        Check(name="credential", outcome="pass", detail=token.describe()),
        Check(
            name="hub_endpoint",
            outcome="pass",
            detail=f"{config.hub.endpoint} is a well-formed https endpoint",
        ),
    ]
    if read_only:
        checks.extend(
            Check(
                name=name,
                outcome="skipped",
                detail="--read-only: this capability can only be proven by exercising it",
            )
            for name in UNPROVABLE_READ_ONLY
        )

    payload: dict[str, Any] = {"checks": [check.as_entry() for check in checks]}
    if options.json_output:
        emit_envelope("doctor", payload, started_at=started_at)
        return
    if not options.quiet:
        width = max(len(check.name) for check in checks)
        for check in checks:
            typer.echo(f"{check.outcome:<7}  {check.name:<{width}}  {check.detail}")


# --------------------------------------------------------------------------- #
# plan and status
# --------------------------------------------------------------------------- #


@app.command()
def plan(ctx: typer.Context, selectors: SelectorArgument = None) -> None:
    """Report the work a sync would do. Mutates nothing and takes no lock."""
    started_at = utc_now()
    options = _options(ctx)
    try:
        config = load_config(options.config_path)
        resolve_token(config.hub, token_file=options.token_file)
        selected = _select(config, selectors)
    except HfcacheError as error:
        _report_failure(ctx, "plan", started_at, error)

    entries = [
        {
            "enabled": repository.enabled,
            "repository_id": repository.id,
            "repository_type": repository.type,
            "requested_revision": repository.revision,
        }
        for repository in selected
        if repository.enabled
    ]
    payload: dict[str, Any] = {"repositories": entries}
    if options.json_output:
        emit_envelope("plan", payload, started_at=started_at)
        return
    if not options.quiet:
        for entry in entries:
            typer.echo(
                f"{entry['repository_type']}:{entry['repository_id']}@{entry['requested_revision']}"
            )


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
    payload: dict[str, Any] = {
        "archive": {
            "archive_id": config.storage.archive_id,
            "root": str(config.storage.archive_root),
        },
        "repositories": entries,
    }
    if options.json_output:
        emit_envelope("status", payload, started_at=started_at)
        return
    if not options.quiet:
        for entry in entries:
            state = "enabled" if entry["enabled"] else "disabled"
            typer.echo(f"{entry['repository_type']}:{entry['repository_id']}  {state}")
