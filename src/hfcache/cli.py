"""Command-line interface for hfcache.

The command surface, global options, JSON envelope, and exit codes are specified
in `docs/cli.md`. Scheduled runs use exactly the same commands an operator types.
"""

import json
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from importlib.util import find_spec
from pathlib import Path
from typing import Annotated, Any

import typer

from hfcache import __version__
from hfcache.identity import new_run_id

__all__ = ["app"]

DEFAULT_CONFIG_PATH = Path("/etc/hfcache/config.toml")
"""Matches the systemd invocation in `docs/plan.md` §22.2."""

ENVELOPE_SCHEMA_VERSION = 1

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
    warnings: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    exit_code: int = 0,
) -> None:
    """Write the single JSON envelope defined by `docs/cli.md` §4 to stdout.

    Serialization follows the durable-schema rules in `docs/schemas.md` §1:
    sorted keys, UTF-8, one trailing newline. Logs and progress go to stderr, so
    piping stdout is always safe.
    """
    warnings = warnings or []
    errors = errors or []
    outcome = "failed" if exit_code else ("success_with_warnings" if warnings else "success")
    envelope = {
        "command": command,
        "completed_at": utc_now(),
        "data": data,
        "errors": errors,
        "exit_code": exit_code,
        "outcome": outcome,
        "run_id": new_run_id(),
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "started_at": started_at,
        "warnings": warnings,
    }
    sys.stdout.write(
        json.dumps(envelope, sort_keys=True, ensure_ascii=False, separators=(",", ": ")) + "\n"
    )


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
    width = max(len(key) for key in payload)
    for key in sorted(payload):
        typer.echo(f"{key.replace('_', ' '):<{width}}  {payload[key]}")
