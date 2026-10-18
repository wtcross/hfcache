"""Command-line interface for hfcache.

The command surface, global options, JSON envelope, and exit codes are specified
in `docs/cli.md`. Scheduled runs use exactly the same commands an operator types.
"""

import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, NoReturn

import typer

from hfcache import cli_client
from hfcache.config import load_config
from hfcache.credentials import resolve_token
from hfcache.errors import (
    CodedError,
    ConfigurationError,
    HfcacheError,
    Problem,
    SafetyError,
)
from hfcache.identity import (
    RunId,
    new_run_id,
)
from hfcache.logging import configure as configure_logging
from hfcache.logging import current_run_id
from hfcache.models import parse_timestamp
from hfcache.reporting import Envelope
from hfcache.services.bootstrap import query_version, validate_config
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.services.requests import (
    UNPROVABLE_READ_ONLY,
    MaintenanceRequest,
    QuarantineRequest,
    RepairRequest,
    VerificationRequest,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hfcache.client import ApiClient
    from hfcache.client_models import ClientEvents


__all__ = ["UNPROVABLE_READ_ONLY", "app"]

DEFAULT_CONFIG_PATH = Path("/etc/hfcache/config.toml")
"""Matches the systemd invocation in docs/security.md hardening posture."""

app = typer.Typer(
    name="hfcache",
    help=("Archive complete revisions of Hugging Face repositories on long-term storage."),
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
    client_config_path: Path | None = None
    api_url: str | None = None
    api_socket: Path | None = None
    api_token_file: Path | None = None
    config_explicit: bool = False
    detach: bool = False
    idempotency_key: str | None = None
    wait_timeout: float | None = None


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
    A command that writes no report has nothing to correlate with and reports the
    id `hfcache.logging` bound at startup — which is what actually ties the
    envelope to that invocation's log lines, rather than minting a second id that
    appears nowhere else.
    """
    result = ServiceResult(command, data, tuple(warnings), tuple(errors), exit_code)
    context = ExecutionContext(
        run_id=RunId(run_id if run_id is not None else (current_run_id() or new_run_id())),
        started_at=parse_timestamp(started_at),
    )
    envelope = result.envelope(context)
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
    evidence = dict(data or {})
    key = getattr(error, "key", None)
    operation_id = getattr(error, "operation_id", None)
    route = getattr(error, "route", None)
    uncertain = (
        operation_id is not None
        or any(problem.code == "HFAPI020" for problem in error.problems)
        or (
            key is not None and getattr(error, "status_code", 0) >= HTTPStatus.INTERNAL_SERVER_ERROR
        )
    )
    if key is not None:
        evidence["idempotency_key"] = key
    if route is not None:
        evidence["route"] = route
    if operation_id is not None:
        evidence |= {"operation_id": operation_id, "work_may_continue": True}
    elif uncertain:
        evidence["work_may_continue"] = True
    if uncertain:
        typer.echo("Accepted work may continue; reconnect using the retained handles", err=True)
    if _options(ctx).json_output:
        emit_envelope(
            command,
            evidence,
            started_at=started_at,
            errors=error.problems,
            exit_code=int(error.exit_code),
        )
    else:
        for problem in error.problems:
            typer.echo(problem.as_line(), err=True)
        if key is not None:
            typer.echo(f"Original idempotency key: {key}", err=True)
        if operation_id is not None:
            typer.echo(f"Operation: {operation_id}; accepted work may continue", err=True)
    raise typer.Exit(int(error.exit_code))


def _echo_pairs(payload: dict[str, Any]) -> None:
    """Print a flat payload as aligned `key  value` lines."""
    width = max(len(key) for key in payload)
    for key in sorted(payload):
        typer.echo(f"{key.replace('_', ' '):<{width}}  {payload[key]}")


def _progress(ctx: typer.Context, page: ClientEvents) -> None:
    """Only bounded, validated server events reach the progress stream."""
    if _options(ctx).quiet:
        return
    if page.truncated:
        typer.echo(f"Event history gap; retained events start at {page.oldest_sequence}", err=True)
    for event in page.events:
        message = "".join(
            character if character.isprintable() else f"\\u{ord(character):04x}"
            for character in event.message
        )
        typer.echo(f"[{event.sequence}] {event.kind}: {message}", err=True)


def _submit(ctx: typer.Context, client: ApiClient, route: str, body: dict[str, Any]) -> Envelope:
    """Keep safety handles visible while the shared client owns observation."""
    options = _options(ctx)
    cli_client.check_job_options(options, submitting=True)
    result = cli_client.submit_job(
        client,
        route,
        body,
        key=options.idempotency_key,
        detach=options.detach,
        timeout=options.wait_timeout,
        on_key=lambda key: typer.echo(f"Idempotency key: {key}", err=True),
        on_accepted=lambda submission: typer.echo(
            f"Operation: {submission.acceptance.operation.operation_id}", err=True
        ),
        on_event=lambda page: _progress(ctx, page),
    )
    if isinstance(result, Envelope):
        return result
    if options.json_output:
        from hfcache.models import serialize  # noqa: PLC0415 - admission-only renderer

        sys.stdout.write(serialize(cli_client.admission_payload(result), indent=None))
    elif not options.quiet:
        typer.echo(f"Accepted operation {result.acceptance.operation.operation_id}")
    raise typer.Exit(0)


operations_app = typer.Typer(
    name="operations", help="Inspect and resume observation of accepted work.", no_args_is_help=True
)
app.add_typer(operations_app)


def _operation_metadata(ctx: typer.Context, identity: str, *, lookup: bool) -> None:
    started_at = utc_now()
    command = "operations lookup" if lookup else "operations show"
    try:
        cli_client.check_job_options(_options(ctx))
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("read", "operations", "operation_history")
            response = (
                client.lookup_response(identity) if lookup else client.operation_response(identity)
            )
        result = response.envelope
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)
    operation = result.data.get("operation", {})
    _show_result(
        ctx,
        result,
        started_at=started_at,
        lines={
            key: str(operation[key])
            for key in ("operation_id", "state", "route")
            if key in operation
        },
    )


@operations_app.command("lookup")
def operations_lookup(
    ctx: typer.Context, key: Annotated[str, typer.Argument(help="Original key.")]
) -> None:
    """Find the receipt using its nonsecret idempotency key."""
    _operation_metadata(ctx, key, lookup=True)


@operations_app.command("show")
def operations_show(ctx: typer.Context, operation_id: str) -> None:
    """Inspect an operation without submitting or waiting."""
    _operation_metadata(ctx, operation_id, lookup=False)


@operations_app.command("wait")
def operations_wait(
    ctx: typer.Context,
    operation_id: str,
    after: Annotated[int, typer.Option("--after", min=0, help="Last observed event sequence.")] = 0,
) -> None:
    """Resume event observation and return the original terminal result."""
    started_at = utc_now()
    options = _options(ctx)
    try:
        cli_client.check_job_options(options, observing=True)
        with cli_client.connect(options) as client:
            client.require_capabilities("read", "operations", "operation_history")
            result = cli_client.observe_operation(
                client,
                operation_id,
                timeout=options.wait_timeout,
                on_event=lambda page: _progress(ctx, page),
                after=after,
            )
    except HfcacheError as error:
        _report_failure(ctx, "operations wait", started_at, error)
    _show_result(
        ctx,
        result,
        started_at=started_at,
        lines={
            "command": result.command,
            "outcome": result.outcome,
            "run id": result.run_id,
        },
    )


def _show_result(
    ctx: typer.Context,
    result: ServiceResult | Envelope,
    *,
    started_at: str,
    lines: dict[str, str] | None = None,
    rows: Sequence[str] = (),
    human_errors: bool = True,
) -> None:
    """Render a classified service result; domain orchestration stays in services."""
    options = _options(ctx)
    if isinstance(result, Envelope):
        if options.json_output:
            sys.stdout.write(cli_client.safe_envelope(result))
            if result.exit_code:
                raise typer.Exit(result.exit_code)
            return
        result = ServiceResult(
            result.command,
            result.data,
            tuple(cli_client.problem(item) for item in result.warnings),
            tuple(cli_client.problem(item) for item in result.errors),
            result.exit_code,
            run_id=RunId(result.run_id),
        )
    if options.json_output:
        emit_envelope(
            result.command,
            result.data,
            started_at=started_at,
            warnings=result.warnings,
            errors=result.errors,
            exit_code=result.exit_code,
            run_id=result.run_id,
        )
    else:
        refusal = bool(
            result.errors
            and not rows
            and not ("report" in result.data and "exit_code" in result.data)
        )
        if not options.quiet and not refusal:
            if lines:
                _echo_pairs(lines)
            for row in rows:
                typer.echo(row)
        if (human_errors and (not options.quiet or refusal)) or not result.data:
            for problem in result.errors:
                typer.echo(problem.as_line(), err=True)
    if result.exit_code:
        raise typer.Exit(result.exit_code)


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path,
        # `readable=False` disables typer's own parse-time access check. It
        # defaults to on, and an existing-but-unreadable path fails it with exit
        # `2` — which `ExitCode` reserves for a malformed command line, precisely
        # so a scheduler can tell one from an application outcome. A
        # configuration file this identity cannot read is an application outcome:
        # `load_config` reports it as `HFCFG001` at exit `10`, naming the path.
        # It also has to be off for the commands that never load configuration —
        # `version` and `--help` must answer on a host where /etc/hfcache is
        # readable only by root and the service account (decision 57).
        typer.Option("--config", metavar="PATH", readable=False, help="Configuration file."),
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
            # Same reason as `--config`: a token file that cannot be read is
            # `HFARG005` at exit `10`, reported by `credentials` by shape and
            # never by content, not a usage error at exit `2`.
            readable=False,
            help="Read a Hub token from this file. Never logged.",
        ),
    ] = None,
    client_config: Annotated[
        Path | None,
        typer.Option(
            "--client-config", metavar="PATH", readable=False, help="API client settings."
        ),
    ] = None,
    api_url: Annotated[
        str | None,
        typer.Option("--api-url", metavar="URL", help="API HTTPS origin and optional path prefix."),
    ] = None,
    api_socket: Annotated[
        Path | None,
        typer.Option("--api-socket", metavar="PATH", readable=False, help="Local API Unix socket."),
    ] = None,
    api_token_file: Annotated[
        Path | None,
        typer.Option(
            "--api-token-file", metavar="PATH", readable=False, help="Protected API bearer file."
        ),
    ] = None,
    detach: Annotated[
        bool, typer.Option("--detach", help="Return the admission receipt without waiting.")
    ] = False,
    idempotency_key: Annotated[
        str | None, typer.Option("--idempotency-key", metavar="KEY", help="Deliberate retry key.")
    ] = None,
    wait_timeout: Annotated[
        float | None,
        typer.Option("--wait-timeout", metavar="SECONDS", help="Observation deadline."),
    ] = None,
) -> None:
    """Options accepted before the command."""
    # Before any command runs, so a failure inside argument handling is still
    # logged, and so `--verbose` selects a level rather than being accepted and
    # ignored. This also binds the run id every event carries; a command that
    # writes a durable report rebinds it to that report's id.
    configure_logging(verbose=verbose, quiet=quiet)
    config_source = ctx.get_parameter_source("config")
    ctx.obj = GlobalOptions(
        config_path=config,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
        # Colour is also suppressed when stdout is not a terminal, so journald
        # never receives escape sequences.
        color=not no_color and sys.stdout.isatty(),
        token_file=token_file,
        client_config_path=client_config,
        api_url=api_url,
        api_socket=api_socket,
        api_token_file=api_token_file,
        config_explicit=config_source is not None and config_source.name == "COMMANDLINE",
        detach=detach,
        idempotency_key=idempotency_key,
        wait_timeout=wait_timeout,
    )


@app.command()
def serve(
    ctx: typer.Context,
    server_config: Annotated[
        Path,
        typer.Option(
            "--server-config", metavar="PATH", readable=False, help="Daemon server configuration."
        ),
    ] = Path("/etc/hfcache/server.toml"),
    hub_token_file: Annotated[
        Path | None,
        typer.Option(
            "--hub-token-file",
            metavar="PATH",
            readable=False,
            help="Explicit server-local Hub credential file for development.",
        ),
    ] = None,
) -> None:
    """Run the authenticated REST server (requires the server installation extra)."""
    started_at = utc_now()
    try:
        options = _options(ctx)
        cli_client.check_job_options(options)
        if options.token_file is not None or options.config_path != DEFAULT_CONFIG_PATH:
            message = (
                "serve uses --server-config; archive policy and Hub credentials "
                "belong to that server policy"
            )
            raise ConfigurationError.single(message, code="HFARG002")
        try:
            from hfcache.server import run  # noqa: PLC0415 - optional server dependency
        except ImportError:
            message = "serve requires the server installation extra"
            raise ConfigurationError.single(message, code="HFCFG005") from None
        run(server_config, hub_token_file=hub_token_file)
    except HfcacheError as error:
        _report_failure(ctx, "serve", started_at, error)


@app.command()
def version(
    ctx: typer.Context,
    server: Annotated[
        bool, typer.Option("--server", help="Report the API writer's version.")
    ] = False,
) -> None:
    """Show application and dependency versions.

    Reads no configuration and touches no archive, so it works on a deployment
    that is otherwise broken.
    """
    started_at = utc_now()
    try:
        cli_client.check_job_options(_options(ctx))
    except HfcacheError as error:
        _report_failure(ctx, "version", started_at, error)
    if server:
        try:
            with cli_client.connect(_options(ctx)) as client:
                client.require_capabilities("read", "reads")
                remote = client.version().envelope
        except HfcacheError as error:
            _report_failure(ctx, "version", started_at, error)
        _show_result(
            ctx,
            remote,
            started_at=started_at,
            lines={key: str(value) for key, value in remote.data.items()},
        )
        return
    payload = query_version().data
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
def config_validate(
    ctx: typer.Context,
    local: Annotated[
        bool, typer.Option("--local", help="Validate on this host for offline bootstrap.")
    ] = False,
) -> None:
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
        cli_client.check_job_options(options)
    except HfcacheError as error:
        _report_failure(ctx, "config validate", started_at, error)
    if not local:
        try:
            cli_client.check_options(options, candidate=True)
            content = (
                cli_client.candidate_content(options.config_path)
                if options.config_explicit
                else None
            )
            with cli_client.connect(options, candidate=True) as client:
                client.require_capabilities("write" if content is not None else "read")
                remote = (
                    client.validate_candidate(content)
                    if content is not None
                    else client.validate_installed()
                )
        except HfcacheError as error:
            _report_failure(ctx, "config validate", started_at, error)
        _show_result(
            ctx,
            remote.envelope,
            started_at=started_at,
            lines={key: str(value) for key, value in remote.envelope.data.items()},
        )
        return
    try:
        config = load_config(options.config_path)
        token = resolve_token(config.hub, token_file=options.token_file)
    except HfcacheError as error:
        _report_failure(ctx, "config validate", started_at, error)

    payload = validate_config(config, token_source=token.source.value).data
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


def _initialize_remote(
    ctx: typer.Context,
    archive_root: Path,
    archive_id: str | None,
    *,
    confirm: bool,
    started_at: str,
) -> Envelope:
    """Adapt explicit confirmation using authenticated writer inspection only."""
    options = _options(ctx)
    if not confirm:
        cli_client.check_job_options(options)
    with cli_client.connect(options) as client:
        client.require_capabilities("read", "reads")
        inspection = client.read("/api/v1/archive/inspection")
        result = inspection.envelope
        if not confirm and result.exit_code:
            return result
        if str(archive_root) != result.data.get("archive_root"):
            message = "Restated archive root does not match the API writer"
            raise ConfigurationError.single(message, code="HFARG002")
        if archive_id is not None and archive_id != inspection.archive_id:
            message = "Restated archive UUID does not match the API writer"
            raise ConfigurationError.single(message, code="HFARG002")
        if confirm:
            capabilities = client.require_capabilities("write", "operations")
            if not capabilities.maintenance_enabled:
                message = "API writer maintenance is disabled; initialization was not submitted"
                raise ConfigurationError.single(message, code="HFAPI002")
            result = _submit(
                ctx,
                client,
                "/api/v1/archive/initializations",
                {
                    "archive_root": str(archive_root),
                    "archive_id": inspection.archive_id,
                    "confirm": True,
                },
            )
        elif not result.exit_code:
            if result.data.get("initializable"):
                refusal = ConfigurationError.single(
                    "--confirm is required; nothing was changed", code="HFARG003"
                )
            else:
                refusal = SafetyError.single(
                    "Archive is already initialized; initialization happens once",
                    code="HFMNT014",
                )
            evidence = result.data | {
                "configured_archive_id": inspection.archive_id,
                "config_fingerprint": inspection.config_fingerprint,
            }
            _report_failure(ctx, "archive init", started_at, refusal, evidence)
    return result


@archive_app.command("init")
def archive_init(
    ctx: typer.Context,
    archive_root: Annotated[
        Path | None,
        typer.Option("--archive-root", metavar="PATH", help="Archive root; must match config."),
    ] = None,
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
    try:
        options = _options(ctx)
        if inspect:
            cli_client.check_job_options(options)
            if confirm or archive_id is not None:
                message = "--inspect does not accept --confirm or --archive-id"
                raise ConfigurationError.single(message, code="HFARG002")
            with cli_client.connect(options) as client:
                client.require_capabilities("read", "reads")
                result = client.read("/api/v1/archive/inspection").envelope
            if archive_root is not None and str(archive_root) != result.data.get("archive_root"):
                message = "Restated archive root does not match the API writer"
                raise ConfigurationError.single(message, code="HFARG002")
        else:
            if archive_root is None:
                message = "Required unless --inspect is selected"
                raise typer.BadParameter(message, param_hint="--archive-root")
            result = _initialize_remote(
                ctx, archive_root, archive_id, confirm=confirm, started_at=started_at
            )
    except HfcacheError as error:
        _report_failure(ctx, "archive init", started_at, error)
    payload = result.data
    if "state" in payload:
        mount = payload["mount"]
        lines = {
            "archive root": payload["archive_root"],
            "state": payload["state"],
            "filesystem": f"{mount['filesystem_type']} from {mount['source']}"
            if mount.get("filesystem_type")
            else "not a mount",
            "initializable": "yes" if payload["initializable"] else "no",
            "existing directories": str(len(payload["existing_directories"])),
            "missing directories": str(len(payload["missing_directories"])),
            "unknown entries": str(payload["unknown_entry_count"]),
            "adopted published": "yes" if payload["adopted_published"] else "no",
        }
    elif payload:
        lines = {
            "archive root": payload["archive_root"],
            "archive id": payload["archive_id"],
            "created": f"{len(payload['created_directories'])} directories",
            "adopted published": "yes" if payload["adopted_published"] else "no",
            "sentinel": str(Path(payload["archive_root"]) / payload["sentinel"]),
        }
    else:
        lines = {}
    _show_result(ctx, result, started_at=started_at, lines=lines)


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
    things (docs/cli.md doctor contract).
    """
    started_at = utc_now()
    try:
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("read" if read_only else "write", "operations")
            result = _submit(ctx, client, "/api/v1/diagnostics", {"read_only": read_only})
    except HfcacheError as error:
        _report_failure(ctx, "doctor", started_at, error)
    checks = result.data.get("checks", [])
    rows: list[str] = []
    if checks:
        width = max(len(check["name"]) for check in checks)
        rows = [
            f"{check['outcome']:<7}  {check['name']:<{width}}  {check['detail']}"
            for check in checks
        ]
    _show_result(ctx, result, started_at=started_at, rows=rows, human_errors=False)


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
    try:
        options = _options(ctx)
        cli_client.check_options(options, candidate=True)
        body: dict[str, Any] = {"selectors": cli_client.selection(selectors or ())}
        if options.config_explicit:
            body["candidate"] = cli_client.candidate_content(options.config_path)
        with cli_client.connect(options, candidate=True) as client:
            client.require_capabilities(
                "write" if options.config_explicit else "read", "operations"
            )
            result = _submit(ctx, client, "/api/v1/plans", body)
    except HfcacheError as error:
        _report_failure(ctx, "plan", started_at, error)
    _show_result(
        ctx,
        result,
        started_at=started_at,
        rows=[_plan_line(entry) for entry in result.data.get("repositories", [])],
        human_errors=False,
    )


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
        cli_client.check_job_options(options)
        query = {"selector": cli_client.selection(selectors or ())}
        with cli_client.connect(options) as client:
            client.require_capabilities("read", "reads")
            result = cli_client.collect(client, "/api/v1/status", "repositories", query)
    except HfcacheError as error:
        _report_failure(ctx, "status", started_at, error)

    if result.exit_code or options.json_output:
        _show_result(ctx, result, started_at=started_at)
        return
    payload = result.data
    archive = payload["archive"]
    entries = payload["repositories"]
    warnings = tuple(cli_client.problem(item) for item in result.warnings)
    if not options.quiet:
        for entry in entries:
            state = (
                ("enabled" if entry["enabled"] else "disabled") if entry["managed"] else "unmanaged"
            )
            typer.echo(
                f"{entry['repository_type']}:{entry['repository_id']}  {state}"
                f"  {entry['verification_state']}"
            )
        if archive["verification"]["degraded"]:
            typer.echo(
                f"archive degraded: {archive['verification']['outstanding_failures']} "
                f"outstanding verification failures",
                err=True,
            )
        for warning in warnings:
            typer.echo(warning.as_line(), err=True)


# --------------------------------------------------------------------------- #
# sync (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@app.command()
def sync(ctx: typer.Context, selectors: SelectorArgument = None) -> None:
    """Synchronize configured repositories (docs/cli.md sync contract).

    The scheduled command, and the only one that downloads. It runs the the sync run contract
    sequence in order: load configuration, take the exclusive lock, prove the
    the preflight contract storage requirements, then process repositories in deterministic
    configuration order, rebuild the derived catalog, and write a durable run
    report.

    The lock and the preflight are held for the whole run rather than checked
    per repository, which is what makes them mean anything: proving the archive
    sound and then letting another command mutate it throughout would prove
    nothing.

    Inside them the run opens its §7.6 journal and reconciles every unfinished
    transaction before a single Hub request is made (`TX-07`). A journal that
    stopped and asked for an operator stops this run at exit `20` with nothing
    downloaded and nothing changed — which is the whole reason an unattended
    scheduled sync is safe to leave running.
    """
    started_at = utc_now()
    try:
        body = {"selectors": cli_client.selection(selectors or ())}
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("write", "operations")
            result = _submit(ctx, client, "/api/v1/syncs", body)
    except HfcacheError as error:
        _report_failure(ctx, "sync", started_at, error)
    rows = [
        f"{item['repository_type']}:{item['repository_id']}  {item['status']}"
        f"{'  ' + item['resolved_commit_sha'] if item['resolved_commit_sha'] else ''}"
        for item in result.data.get("repositories", [])
    ]
    _show_result(ctx, result, started_at=started_at, rows=rows)


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
        cli_client.check_job_options(options)
        query: dict[str, Any] = {"selector": cli_client.selection(selectors or ())}
        if repository_type is not None:
            if repository_type not in {"model", "dataset"}:
                message = "--type requires model or dataset"
                raise ConfigurationError.single(message, code="HFARG002")
            query["type"] = repository_type
        with cli_client.connect(options) as client:
            client.require_capabilities("read", "reads")
            result = cli_client.inventory(client, query, revisions=revisions)
    except HfcacheError as error:
        _report_failure(ctx, "list", started_at, error)

    entries = result.data.get("repositories", [])
    _show_result(
        ctx,
        result,
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
    """Re-read published content and compare it with its manifest (docs/cli.md verification
    contract).

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
    mutually exclusive with sync, prune, purge, and repair, and runs with Hub
    networking disabled because it re-reads what the archive already has.

    `--revision TYPE:ID@SHA` checks one retained revision, which is what an
    operator reaches for after a `--full` reported a finding and again after a
    `repair` claims to have fixed it. The repository need not be in
    configuration: an unmanaged repository's data is still the archive's (`AD-06`)
    and is still worth checking.

    `--estimate` hashes nothing and takes no lock. It reports what `--full`
    would read, so that scheduling it against a NAS maintenance window is a
    decision made from a measurement rather than from a guess (docs/cli.md verification contract).
    """
    started_at = utc_now()
    request = VerificationRequest(
        new=new, full=full, revision=revision, estimate=estimate, run_id=run_id
    )
    try:
        mode = request.mode
        if mode == "estimate":
            cli_client.check_job_options(_options(ctx))
            with cli_client.connect(_options(ctx)) as client:
                client.require_capabilities("read", "reads")
                result = client.read("/api/v1/verification/estimate").envelope
        else:
            request.validate_scope()
            with cli_client.connect(_options(ctx)) as client:
                client.require_capabilities("write", "operations")
                result = _submit(
                    ctx,
                    client,
                    "/api/v1/verifications",
                    {
                        "mode": mode,
                        "revision": revision,
                        "run_id": run_id,
                    },
                )
    except HfcacheError as error:
        _report_failure(ctx, request.command, started_at, error)
    payload = result.data
    lines: dict[str, str] = {}
    if mode == "estimate" and payload:
        duration = payload["estimated_duration_seconds"]
        lines = {
            "repositories": str(payload["repositories"]),
            "revisions": str(payload["revisions"]),
            "unique objects": str(payload["unique_objects"]),
            "unique bytes": _bytes(payload["unique_bytes"]),
            "estimated duration": f"{duration:.0f}s"
            if duration is not None
            else "unknown — never measured",
            "storage maintenance": payload["storage_maintenance"],
        }
    elif "report" in payload:
        scope = payload["scope"]
        lines = {
            "outcome": payload["verification_outcome"],
            "repositories": str(scope["repositories"]),
            "revisions": str(scope["revisions"]),
            "objects read": str(scope["unique_objects_read"]),
            "bytes read": _bytes(scope["unique_bytes_read"]),
            "findings": str(len(payload["findings"])),
            "report": payload["report"],
        }
    _show_result(ctx, result, started_at=started_at, lines=lines)


# --------------------------------------------------------------------------- #
# quarantine (`docs/cli.md` §2, decision 103)
# --------------------------------------------------------------------------- #


@app.command()
def quarantine(
    ctx: typer.Context,
    transaction_ids: Annotated[
        list[str] | None,
        typer.Argument(help="Explicit transaction ids of abandoned staging quarantine entries."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate the exact cleanup plan and mutate nothing."),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Permanently remove the proven redundant quarantine entries."),
    ] = False,
) -> None:
    """Clean explicitly selected abandoned staging after proving its content redundant."""
    started_at = utc_now()
    command = f"quarantine {'--apply' if apply else '--dry-run'}"
    try:
        if dry_run == apply:
            message = "exactly one of --dry-run and --apply is required"
            raise ConfigurationError.single(message, code="HFARG002")
        if not transaction_ids:
            message = "quarantine cleanup requires explicit transaction ids"
            raise ConfigurationError.single(message, code="HFARG003")
        QuarantineRequest(tuple(transaction_ids), dry_run=dry_run, apply=apply).validate_scope()
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("write" if apply else "read", "operations")
            result = _submit(
                ctx,
                client,
                "/api/v1/quarantine-cleanups" if apply else "/api/v1/quarantine-plans",
                {"transaction_ids": transaction_ids},
            )
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)
    lines = {
        item["transaction_id"]: "already absent"
        if item["already_absent"]
        else f"{len(item['files'])} redundant files, {item['logical_bytes']} logical bytes"
        for item in result.data.get("plans", [])
    }
    _show_result(ctx, result, started_at=started_at, lines=lines)


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
    """Inspect or complete retention cleanup (docs/architecture.md retention contract).

    Retention normally runs inside `sync`; this command exists to inspect the
    plan before it runs and to complete retention an earlier failure deferred
    (`docs/cli.md` §2).

    `--dry-run` reads only and takes no lock: it reports the plan `--apply`
    would execute, built from the same references and manifests the prune itself
    reads, so what an operator reviewed is what runs.

    `--apply` mutates, so it takes the exclusive lock and passes the same the preflight contract
    preflight as any other mutating command, and plans *inside* them — a plan
    made before the lock could be stale by the time it ran.
    """
    started_at = utc_now()
    command = f"prune {'--apply' if apply else '--dry-run'}"
    try:
        request = MaintenanceRequest(selectors=tuple(selectors or ()), dry_run=dry_run, apply=apply)
        request.require_mode()
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("write" if apply else "read", "operations")
            result = _submit(
                ctx,
                client,
                "/api/v1/prunes" if apply else "/api/v1/prune-plans",
                {
                    "selectors": cli_client.selection(request.selectors),
                },
            )
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)
    lines = {
        f"{item['repository_type']}:{item['repository_id']}": (
            f"prune generation {item['selected']['publication_generation']} "
            f"({item['selected']['commit_sha']})"
        )
        for item in result.data.get("plans", [])
    } or {"retention": "nothing to prune"}
    _show_result(ctx, result, started_at=started_at, lines=lines)


# --------------------------------------------------------------------------- #
# purge (`docs/cli.md` §2, `AD-20`)
# --------------------------------------------------------------------------- #


@app.command()
def purge(
    ctx: typer.Context,
    selectors: SelectorArgument = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the exact purge plan and mutate nothing."),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Execute the validated purge plan."),
    ] = False,
    all_unmanaged: Annotated[
        bool,
        typer.Option(
            "--all-unmanaged",
            help="Select every archived repository absent from configuration.",
        ),
    ] = False,
) -> None:
    """Permanently remove explicitly selected unmanaged repositories (`AD-20`)."""
    started_at = utc_now()
    command = f"purge {'--apply' if apply else '--dry-run'}"
    try:
        request = MaintenanceRequest(
            selectors=tuple(selectors or ()),
            dry_run=dry_run,
            apply=apply,
            all_unmanaged=all_unmanaged,
        )
        request.require_mode()
        if all_unmanaged and request.selectors:
            message = "--all-unmanaged and repository selectors are mutually exclusive"
            raise ConfigurationError.single(message, code="HFARG002")
        if not all_unmanaged and not request.selectors:
            message = "purge requires repository selectors or --all-unmanaged"
            raise ConfigurationError.single(message, code="HFARG003")
        selected = cli_client.selection(request.selectors)
        if any("@" in selector for selector in request.selectors):
            message = "purge removes whole repositories; revision-qualified selectors are refused"
            raise ConfigurationError.single(message, code="HFARG001")
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("write" if apply else "read", "operations")
            result = _submit(
                ctx,
                client,
                "/api/v1/purges" if apply else "/api/v1/purge-plans",
                {
                    "selectors": selected,
                    "all_unmanaged": all_unmanaged,
                },
            )
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)
    lines = {
        f"{item['repository_type']}:{item['repository_id']}": (
            f"purge {len(item['revisions'])} revisions, "
            f"{_bytes(item['unique_bytes_released_estimate'])} logical"
        )
        for item in result.data.get("plans", [])
    } or {"purge": "nothing to purge"}
    _show_result(ctx, result, started_at=started_at, lines=lines)


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
    """Reconcile unfinished transaction journals (docs/architecture.md recovery contract).

    Roll-forward oriented: it never replaces an expected digest, chooses a
    revision by modification time, or removes unknown data (`AD-16`). A state it
    may not resolve on its own is reported and exits `20` rather than guessed at,
    because a state two valid executions could both have produced has no single
    correct resolution.

    `--dry-run` reads only. `--apply` takes the same exclusive lock and runs the
    same storage preflight every mutating command does, because it is one.
    """
    started_at = utc_now()
    command = f"recover {'--apply' if apply else '--dry-run'}"
    try:
        request = MaintenanceRequest(dry_run=dry_run, apply=apply)
        request.require_mode()
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("write" if apply else "read", "operations")
            result = _submit(
                ctx, client, "/api/v1/recoveries" if apply else "/api/v1/recovery-plans", {}
            )
    except HfcacheError as error:
        _report_failure(ctx, command, started_at, error)
    payload = result.data
    lines = (
        {
            "actionable": str(payload["actionable"]),
            "blocked": str(payload["blocked"]),
            "applied": str(payload.get("applied", "-")),
        }
        if "actionable" in payload
        else {}
    )
    _show_result(ctx, result, started_at=started_at, lines=lines)


@app.command()
def repair(
    ctx: typer.Context,
    selector: Annotated[
        str,
        typer.Argument(metavar="TYPE:ID@SHA", help="The retained revision to replace."),
    ],
    reason: Annotated[
        str,
        typer.Option("--reason", metavar="TEXT", help="Why this repair is being performed."),
    ] = "operator_requested",
) -> None:
    """Replace a damaged publication instance with a verified one (docs/cli.md verification
    contract).

    The exact immutable SHA is downloaded into an isolated
    `.store/repair/<transaction-id>/hub` and checked against the **original**
    manifest. If any expected digest differs the command stops with `HFRET006`
    and the published revision is unchanged: newly observed bytes are evidence of
    a failed repair, never a new expectation (`AD-13`).

    The replacement is published under a new publication id at a new immutable
    locator, re-verified where it now lives, and only then do the references
    switch. The superseded instance stays readable at its original locator for
    the configured grace period, so a consumer copy already in flight can finish;
    after that a checkpointed cleanup *quarantines* it rather than deleting it,
    and `recover --apply` is what performs that.
    """
    started_at = utc_now()
    try:
        request = RepairRequest(selector, reason=reason)
        with cli_client.connect(_options(ctx)) as client:
            client.require_capabilities("write", "operations")
            result = _submit(
                ctx,
                client,
                "/api/v1/repairs",
                {
                    "revision": request.selector,
                    "reason": request.reason,
                },
            )
    except CodedError as error:
        _report_failure(
            ctx, "repair", started_at, ConfigurationError.single(str(error), code=error.code)
        )
    except HfcacheError as error:
        _report_failure(ctx, "repair", started_at, error)
    payload = result.data
    lines = (
        {
            "commit sha": payload["commit_sha"],
            "retired": payload["retired_publication_id"],
            "replacement": payload["replacement_publication_id"],
            "grace expires": datetime.fromisoformat(payload["grace_expires_at"]).isoformat(),
            "transaction": payload["transaction_id"],
        }
        if payload
        else {}
    )
    _show_result(ctx, result, started_at=started_at, lines=lines)
