"""CLI transport helpers preserve server evidence without writer access (decision 119)."""

import os
import stat
from typing import TYPE_CHECKING, Any

from hfcache.client import ApiClient
from hfcache.client_config import resolve_client_config
from hfcache.client_errors import ClientProtocolError
from hfcache.errors import CodedError, ConfigurationError, Problem
from hfcache.identity import parse_selector
from hfcache.models import serialize
from hfcache.redaction import sanitize

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from hfcache.cli import GlobalOptions
    from hfcache.client_models import ClientRead
    from hfcache.reporting import Envelope, EnvelopeProblem

_MAX_CANDIDATE_BYTES = 1048576


def check_options(options: GlobalOptions, *, candidate: bool = False) -> None:
    """Refuse migrated options before candidate-file or credential access."""
    if options.token_file is not None:
        message = "API commands use --api-token-file; --token-file is only for local Hub validation"
        raise ConfigurationError.single(message, code="HFARG002")
    if options.config_explicit and not candidate:
        message = (
            "--config supplies a candidate only for config validate or plan; use --client-config"
        )
        raise ConfigurationError.single(message, code="HFARG002")


def connect(options: GlobalOptions, *, candidate: bool = False) -> ApiClient:
    """Resolve management settings only after rejecting legacy credential overrides."""
    check_options(options, candidate=candidate)
    settings = resolve_client_config(
        options.client_config_path,
        api_url=options.api_url,
        api_socket=options.api_socket,
        api_token_file=options.api_token_file,
    )
    return ApiClient(settings)


def candidate_content(path: Path) -> str:
    """Read bounded UTF-8 content, never a writer pathname or proposed credential."""
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= _MAX_CANDIDATE_BYTES:
            message = "Candidate must be a nonempty regular file of at most 1 MiB"
            raise ConfigurationError.single(message, code="HFARG002")
        raw = bytearray()
        while len(raw) <= _MAX_CANDIDATE_BYTES:
            part = os.read(descriptor, min(65536, _MAX_CANDIDATE_BYTES + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
        after = os.fstat(descriptor)
        if len(raw) != before.st_size or (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            message = "Candidate changed while being read"
            raise ConfigurationError.single(message, code="HFARG002")
        return raw.decode("utf-8")
    except OSError, UnicodeError:
        message = "Candidate file is unavailable or is not UTF-8"
        raise ConfigurationError.single(message, code="HFCFG001") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def selection(values: Sequence[str]) -> list[str]:
    """Grammar only; the server owns configured/unmanaged membership decisions."""
    try:
        return [parse_selector(value).identity.selector for value in values]
    except CodedError as error:
        raise ConfigurationError.single(str(error), code=error.code) from None


def collect(
    client: ApiClient, path: str, field: str, params: Mapping[str, Any] | None = None
) -> Envelope:
    """Retain the first Envelope's invocation metadata and require complete pages."""
    return _collect(client, path, field, params)[1]


def _collect(
    client: ApiClient, path: str, field: str, params: Mapping[str, Any] | None = None
) -> tuple[ClientRead, Envelope]:
    first = None
    rows = []
    budget = 0
    for page in client.iter_pages(path, field, params):
        if page.envelope.exit_code:
            return page, page.envelope
        if first is None:
            first = page
        budget += len(serialize(page.envelope.data[field]).encode("utf-8"))
        if budget > client.config.max_response_bytes:
            raise ClientProtocolError
        rows.extend(page.envelope.data[field])
    if first is None:
        raise ClientProtocolError
    return first, first.envelope.model_copy(update={"data": first.envelope.data | {field: rows}})


def inventory(client: ApiClient, params: Mapping[str, Any], *, revisions: bool) -> Envelope:
    """Join revision pages without losing configured-but-empty or unmanaged rows."""
    try:
        return _inventory(client, params, revisions=revisions)
    except KeyError, TypeError, ValueError:
        raise ClientProtocolError from None


def _inventory(client: ApiClient, params: Mapping[str, Any], *, revisions: bool) -> Envelope:
    first, result = _collect(client, "/api/v1/repositories", "repositories", params)
    if result.exit_code:
        return result
    rows = result.data["repositories"]
    if not revisions:
        return result
    budget = len(serialize(rows).encode("utf-8"))
    targets = {}
    for row in rows:
        identity = (row["repository_type"], row["repository_id"])
        targets[identity] = dict(row) | {"revisions": []}
    for page in client.iter_pages("/api/v1/repositories/revisions", "revisions", params):
        if page.envelope.exit_code:
            return page.envelope
        if (
            page.archive_id != first.archive_id
            or page.config_fingerprint != first.config_fingerprint
        ):
            raise ClientProtocolError
        budget += len(serialize(page.envelope.data["revisions"]).encode("utf-8"))
        if budget > client.config.max_response_bytes:
            raise ClientProtocolError
        for revision in page.envelope.data["revisions"]:
            item = dict(revision)
            identity = (item.pop("repository_type"), item.pop("repository_id"))
            if identity not in targets:
                raise ClientProtocolError
            targets[identity]["revisions"].append(item)
    joined = list(targets.values())
    for row in joined:
        held = row["revisions"]
        current = (row["current_commit_sha"], row["current_publication_id"])
        if (
            len(held) != row["retained_revisions"]
            or len({entry["commit_sha"] for entry in held}) != len(held)
            or (
                current != (None, None)
                and current
                not in {(entry["commit_sha"], entry["publication_id"]) for entry in held}
            )
            or [entry["publication_generation"] for entry in held]
            != sorted(entry["publication_generation"] for entry in held)
        ):
            raise ClientProtocolError
    if len(serialize(joined).encode("utf-8")) > client.config.max_response_bytes:
        raise ClientProtocolError
    return result.model_copy(update={"data": {"repositories": joined}})


def run_job(
    client: ApiClient,
    path: str,
    body: Mapping[str, Any],
    *,
    on_key: Callable[[str], None] | None = None,
) -> Envelope:
    submitted = client.submit(path, body, on_key=on_key)
    return client.poll(submitted.acceptance.operation.operation_id).envelope


def problem(value: EnvelopeProblem) -> Problem:
    context = dict(value.context)
    location = context.pop("location", None)
    return Problem(value.code, value.message, location, value.repository, context)


def safe_envelope(envelope: Envelope) -> str:
    """Preserve evidence fields while applying the common presentation redaction."""
    return serialize(sanitize(envelope.to_payload()), indent=None)
