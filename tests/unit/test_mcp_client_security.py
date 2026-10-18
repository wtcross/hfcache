"""MCP-004 example refuses unsafe setup, untrusted replies and bearer forwarding."""

import asyncio
import importlib.util
import io
import logging
import os
import ssl
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx2
import pytest

from tests.fixtures import examples
from tests.unit.test_server_bootstrap import isolate_logging  # noqa: F401 - autouse fixture

ROOT = Path(__file__).parents[2]
TOKEN = "example-mcp-reader-" + "T" * 48
PRIVATE = "unregistered-server-response-DO-NOT-ECHO"
ENDPOINT = "https://archive.example/mcp/"


@pytest.fixture
def example(monkeypatch):
    name = "hfcache_mcp_example_security"
    spec = importlib.util.spec_from_file_location(name, ROOT / "examples" / "mcp-client.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def settings(example, tmp_path):
    path = tmp_path / "mcp.token"
    path.write_text(TOKEN, encoding="ascii")
    path.chmod(0o600)
    return example.Settings(endpoint=ENDPOINT, token_file=path)


def frame(
    *, cursor=None, archive_id=examples.ARCHIVE_ID, fingerprint=examples.FINGERPRINT, data=None
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": "a" * 32,
        "archive_id": archive_id,
        "config_fingerprint": fingerprint,
        "next_cursor": cursor,
        "envelope": {
            "schema_version": 1,
            "command": "list",
            "run_id": "b" * 32,
            "started_at": "2026-10-18T12:00:00Z",
            "completed_at": "2026-10-18T12:00:00Z",
            "outcome": "success",
            "exit_code": 0,
            "errors": [],
            "warnings": [],
            "data": {"repositories": [{"repository_type": "model", "repository_id": "org/model"}]}
            if data is None
            else data,
        },
    }


@dataclass
class Reply:
    structured_content: dict | None
    is_error: bool = False


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        self.closed = True

    async def call_tool(self, name, arguments, *, raise_on_error):
        assert raise_on_error is False
        self.calls.append((name, dict(arguments)))
        response = self.replies.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("endpoint", "https://user:secret@archive.example/mcp/"),
        ("endpoint", ENDPOINT + "?token=" + TOKEN),
        ("endpoint", ENDPOINT + "#" + PRIVATE),
        ("endpoint", "https://archive.example/../mcp/"),
        ("endpoint", "https://archive.example/%2e%2e/mcp/"),
        ("endpoint", "https://archive.example/\r\nmcp/"),
        ("endpoint", "http://archive.example/mcp/"),
        ("endpoint", "file:///etc/" + PRIVATE + "/mcp/"),
        ("endpoint", "https://archive.example/mcp"),
        ("page_size", True),
        ("page_size", 0),
        ("page_size", 10001),
        ("max_pages", True),
        ("max_pages", 0),
        ("max_pages", 10001),
        ("timeout_seconds", True),
        ("timeout_seconds", 0),
        ("timeout_seconds", float("inf")),
        ("timeout_seconds", float("nan")),
        ("mode", PRIVATE),
        ("expected_archive_id", PRIVATE),
        ("repository_id", "org/model"),
        ("repository_type", "model"),
    ],
)
def test_example_setup_rejects_unsafe_values_without_echo(example, settings, key, value):
    values = {field: getattr(settings, field) for field in settings.__dataclass_fields__}
    values[key] = value
    with pytest.raises(example.ExampleError) as error:
        example.Settings(**values)
    assert str(error.value) == example.FAILURE
    assert TOKEN not in str(error.value)
    assert PRIVATE not in str(error.value)


@pytest.mark.parametrize("damage", ["missing", "mode", "symlink", "parent", "fifo", "hub", "large"])
def test_bad_protected_credential_refuses_before_any_client_or_ambient_fallback(
    example, settings, tmp_path, monkeypatch, damage
):
    path = settings.token_file
    if damage == "missing":
        path.unlink()
    elif damage == "mode":
        path.chmod(0o644)
    elif damage in {"symlink", "parent"}:
        held = tmp_path / "held"
        held.mkdir()
        target = held / "token"
        path.rename(target)
        if damage == "symlink":
            path.symlink_to(target)
        else:
            alias = tmp_path / "alias"
            alias.symlink_to(held, target_is_directory=True)
            settings = example.Settings(endpoint=ENDPOINT, token_file=alias / "token")
    elif damage == "fifo":
        path.unlink()
        os.mkfifo(path, 0o600)
    else:
        path.write_text("hf_" + "x" * 48 if damage == "hub" else "x" * 4097, encoding="ascii")
    for name in ("HF_TOKEN", "HFCACHE_MCP_TOKEN", "HFCACHE_API_TOKEN"):
        monkeypatch.setenv(name, TOKEN)
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path))

    def forbidden(*_args):
        pytest.fail("unusable selected credential reached a client")

    with pytest.raises(example.ExampleError) as error:
        asyncio.run(example.run(settings, client_factory=forbidden))
    assert str(error.value) == example.FAILURE
    assert TOKEN not in str(error.value)


@pytest.mark.parametrize(
    "damage",
    [
        "version_missing",
        "version_bool",
        "version_future",
        "envelope_version",
        "extra",
        "null_archive",
        "null_fingerprint",
        "failed_envelope",
        "no_rows",
        "rpc_error",
        "no_content",
    ],
)
def test_example_untrusted_wire_is_fixed_failure_and_never_a_success_summary(
    example, settings, damage
):
    source = frame()
    if damage == "version_missing":
        del source["schema_version"]
    elif damage in {"version_bool", "version_future"}:
        source["schema_version"] = True if damage == "version_bool" else 2
    elif damage == "envelope_version":
        del source["envelope"]["schema_version"]
    elif damage == "extra":
        source[PRIVATE] = TOKEN
    elif damage == "null_archive":
        source["archive_id"] = None
    elif damage == "null_fingerprint":
        source["config_fingerprint"] = None
    elif damage == "failed_envelope":
        source["envelope"] |= {
            "outcome": "failed",
            "exit_code": 20,
            "errors": [
                {
                    "code": "HFAPI005",
                    "message": PRIVATE + TOKEN,
                    "context": {},
                    "repository": None,
                }
            ],
        }
    elif damage == "no_rows":
        source["envelope"]["data"] = {"repositories": PRIVATE}
    client = FakeClient([Reply(None if damage == "no_content" else source, damage == "rpc_error")])
    with pytest.raises(example.ExampleError) as error:
        asyncio.run(example.run(settings, client_factory=lambda *_: client))
    assert str(error.value) == example.FAILURE
    assert client.closed


@pytest.mark.parametrize(
    "damage", ["archive", "fingerprint", "cycle", "secret_cursor", "empty", "max_pages"]
)
def test_example_walk_refuses_identity_changes_cycles_and_incomplete_pages(
    example, settings, damage
):
    first, second = frame(cursor="cursor-1"), frame()
    if damage == "archive":
        second["archive_id"] = "ffffffff-ffff-4fff-8fff-ffffffffffff"
    elif damage == "fingerprint":
        second["config_fingerprint"] = "c" * 64
    elif damage == "cycle":
        second["next_cursor"] = "cursor-1"
    elif damage == "secret_cursor":
        first["next_cursor"] = TOKEN
    elif damage == "empty":
        first["envelope"]["data"]["repositories"] = []
    else:
        settings = example.Settings(endpoint=ENDPOINT, token_file=settings.token_file, max_pages=1)
    client = FakeClient([Reply(first), Reply(second)])
    with pytest.raises(example.ExampleError):
        asyncio.run(example.run(settings, client_factory=lambda *_: client))
    assert client.closed
    assert len(client.calls) == (1 if damage in {"secret_cursor", "empty", "max_pages"} else 2)


def test_expected_archive_uuid_is_checked_before_page_callback(example, settings):
    settings = example.Settings(
        endpoint=ENDPOINT,
        token_file=settings.token_file,
        expected_archive_id="ffffffff-ffff-4fff-8fff-ffffffffffff",
    )
    client = FakeClient([Reply(frame())])
    observed = []
    with pytest.raises(example.ExampleError):
        asyncio.run(
            example.run(
                settings,
                client_factory=lambda *_: client,
                on_page=lambda *page: observed.append(page),
            )
        )
    assert observed == []
    assert client.closed


def test_example_failure_suppresses_descendant_diagnostics_and_restores_caller_logging(
    example, settings, capfd
):
    logger = logging.getLogger("fastmcp.client.security-fixture")
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    logger.addHandler(handler)
    filters = tuple(handler.filters)
    disabled = logger.disabled

    class NoisyClient(FakeClient):
        async def call_tool(self, *_args, **_kwargs):
            logger.error("server says %s %s", PRIVATE, TOKEN, exc_info=True)
            raise RuntimeError(PRIVATE + TOKEN)

    try:
        client = NoisyClient([])
        with pytest.raises(example.ExampleError) as error:
            asyncio.run(example.run(settings, client_factory=lambda *_: client))
        assert str(error.value) == example.FAILURE
        assert tuple(handler.filters) == filters
        assert logger.disabled == disabled
        assert output.getvalue() == ""
        logger.warning("caller logging restored")
        assert output.getvalue().strip() == "caller logging restored"
    finally:
        logger.removeHandler(handler)
        handler.close()
    captured = capfd.readouterr()
    assert PRIVATE not in captured.out + captured.err
    assert TOKEN not in captured.out + captured.err


@pytest.mark.parametrize("failure", ["connect", "call", "timeout"])
def test_example_connection_call_and_deadline_errors_have_one_safe_diagnostic(
    example, settings, failure
):
    class WaitingClient(FakeClient):
        async def call_tool(self, *_args, **_kwargs):
            await asyncio.Event().wait()
            pytest.fail("unbounded example call")

    def factory(*_args):
        if failure == "connect":
            raise RuntimeError(PRIVATE + TOKEN)
        return (
            WaitingClient([])
            if failure == "timeout"
            else FakeClient([RuntimeError(PRIVATE + TOKEN)])
        )

    if failure == "timeout":
        settings = example.Settings(
            endpoint=ENDPOINT, token_file=settings.token_file, timeout_seconds=0.01
        )
    with pytest.raises(example.ExampleError) as error:
        asyncio.run(example.run(settings, client_factory=factory))
    assert str(error.value) == example.FAILURE


def test_example_http_factory_forces_verified_tls_no_proxy_and_no_sdk_redirects(
    example, settings, monkeypatch
):
    original = httpx2.AsyncClient
    captured = {}

    def construct(**options):
        captured.update(options)
        return original(**options)

    monkeypatch.setattr(example.httpx2, "AsyncClient", construct)
    monkeypatch.setenv("HTTPS_PROXY", "http://" + PRIVATE + ".invalid")
    client = example.make_client(settings, TOKEN)
    factory = client.transport.httpx_client_factory

    async def check():
        async with factory(headers={"Authorization": "Bearer " + TOKEN}, follow_redirects=True):
            assert captured["follow_redirects"] is False
            assert captured["trust_env"] is False
            assert captured["headers"]["Accept-Encoding"] == "identity"
            assert isinstance(captured["verify"], ssl.SSLContext)
            assert captured["verify"].verify_mode == ssl.CERT_REQUIRED
            assert captured["verify"].check_hostname is True

    asyncio.run(check())


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_example_never_follows_redirect_or_forwards_bearer(example, settings, monkeypatch, status):
    original = httpx2.AsyncClient
    seen = []

    async def request(message):
        seen.append(message)
        return httpx2.Response(status, headers={"location": "https://" + PRIVATE + ".invalid/mcp/"})

    def construct(**options):
        return original(**options, transport=httpx2.MockTransport(request))

    monkeypatch.setattr(example.httpx2, "AsyncClient", construct)
    sdk = example.make_client(settings, TOKEN)

    async def check():
        async with sdk.transport.httpx_client_factory(
            headers={"Authorization": "Bearer " + TOKEN}, follow_redirects=True
        ) as client:
            with pytest.raises(example.ExampleError):
                await client.get(ENDPOINT)
        assert len(seen) == 1
        assert str(seen[0].url) == ENDPOINT
        assert seen[0].headers["authorization"] == "Bearer " + TOKEN

    asyncio.run(check())


def publication_frames():
    reference = examples.reference().model_dump(mode="json")
    manifest = examples.manifest().model_dump(mode="json")
    header = {key: value for key, value in manifest.items() if key not in {"files", "dependencies"}}
    responses = [frame(), frame(data={"locator_base": "published/", "reference": reference})]
    responses[1]["envelope"]["command"] = "reference read"
    for collection in ("files", "dependencies"):
        response = frame(
            data={
                "projection": True,
                "manifest": dict(header),
                "collection": collection,
                "entries": manifest[collection],
                "total_entries": len(manifest[collection]),
                "tree_base": "archive-root/",
            }
        )
        response["envelope"]["command"] = "manifest read"
        responses.append(response)
    return responses


@pytest.mark.parametrize(
    "damage",
    [
        "command",
        "reference_repository",
        "reference_version",
        "current_cursor",
        "manifest_schema",
        "manifest_repository",
        "manifest_generation",
        "manifest_publication",
        "projection",
        "collection",
        "tree_base",
        "header_disagreement",
        "bool_total",
        "bool_count",
    ],
)
def test_example_exact_publication_rejects_wrong_schema_identity_projection_and_boolean_counts(  # noqa: PLR0912 - distinct untrusted publication boundaries
    example, settings, damage
):
    settings = example.Settings(
        endpoint=ENDPOINT,
        token_file=settings.token_file,
        repository_type="model",
        repository_id=examples.REPOSITORY_ID,
    )
    responses = publication_frames()
    reference = responses[1]["envelope"]["data"]["reference"]
    projected = responses[2]["envelope"]["data"]
    if damage == "command":
        responses[0]["envelope"]["command"] = "sync"
    elif damage == "reference_repository":
        reference["repository_id"] = "other/repository"
    elif damage == "reference_version":
        reference["schema_version"] = True
    elif damage == "current_cursor":
        responses[1]["next_cursor"] = "continuation-not-valid-for-exact-reference"
    elif damage == "manifest_schema":
        projected["manifest"]["schema_version"] = 2
    elif damage == "manifest_repository":
        projected["manifest"]["repository_id"] = "other/repository"
    elif damage == "manifest_generation":
        projected["manifest"]["publication_generation"] += 1
    elif damage == "manifest_publication":
        projected["manifest"]["publication_id"] = "d" * 32
    elif damage == "projection":
        projected["projection"] = False
    elif damage == "collection":
        projected["collection"] = "dependencies"
    elif damage == "tree_base":
        projected["tree_base"] = "published/"
    elif damage == "header_disagreement":
        responses[3]["envelope"]["data"]["manifest"]["application_version"] = PRIVATE
    elif damage == "bool_total":
        responses[3]["envelope"]["data"]["total_entries"] = True
    else:
        projected["manifest"]["file_count"] = True
    client = FakeClient([Reply(response) for response in responses])
    with pytest.raises(example.ExampleError) as error:
        asyncio.run(example.run(settings, client_factory=lambda *_: client))
    assert str(error.value) == example.FAILURE
    assert client.closed


@pytest.mark.parametrize("damage", ["too_many", "duplicate", "descending"])
def test_example_inventory_must_be_bounded_and_have_strictly_ordered_unique_rows(
    example, settings, damage
):
    first = frame(cursor="continue")
    second = frame()
    if damage == "too_many":
        settings = example.Settings(endpoint=ENDPOINT, token_file=settings.token_file, page_size=1)
        first["envelope"]["data"]["repositories"].append(
            {"repository_type": "model", "repository_id": "org/second"}
        )
    elif damage == "descending":
        second["envelope"]["data"]["repositories"][0]["repository_id"] = "aaa/model"
    client = FakeClient([Reply(first), Reply(second)])
    with pytest.raises(example.ExampleError):
        asyncio.run(example.run(settings, client_factory=lambda *_: client))
    assert client.closed


class Body(httpx2.AsyncByteStream):
    def __init__(self):
        self.closed = False
        self.reads = 0

    async def __aiter__(self):
        for part in (b"1234", b"5678", b"9"):
            self.reads += 1
            yield part

    async def aclose(self):
        self.closed = True


@pytest.mark.parametrize(
    "headers",
    [
        {"content-encoding": "gzip"},
        {"content-encoding": "deflate"},
        {"content-type": "text/html"},
        {"content-length": "99999999999999999999999999"},
        {"content-length": "9"},
        {"content-length": "3"},
        {},
    ],
)
def test_example_transport_bounds_native_bytes_and_closes_rejected_or_lying_responses(
    example, settings, monkeypatch, headers
):
    original = httpx2.AsyncClient
    stream = Body()

    async def request(_message):
        return httpx2.Response(
            200, headers={"content-type": "application/json"} | headers, stream=stream
        )

    def construct(**options):
        return original(**options, transport=httpx2.MockTransport(request))

    monkeypatch.setattr(example.httpx2, "AsyncClient", construct)
    monkeypatch.setattr(example, "MAX_RESPONSE_BYTES", 8)
    sdk = example.make_client(settings, TOKEN)

    async def check():
        async with sdk.transport.httpx_client_factory() as client:
            with pytest.raises(example.ExampleError):
                await client.get(ENDPOINT)
        assert stream.closed
        if not headers or headers == {"content-length": "3"}:
            assert stream.reads == 3
        else:
            assert stream.reads == 0

    asyncio.run(check())


def test_example_main_rejects_literal_token_arguments_without_echo(example, capsys):
    assert example.main(["--url", ENDPOINT, "--token", TOKEN]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == example.FAILURE
    assert TOKEN not in captured.err
