"""Explicit installed-writer HTTP harness; no argv reinterpretation or local fallback."""

import os
import re
import socket
import threading
import warnings
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import pytest
from starlette.exceptions import StarletteDeprecationWarning
from typer.testing import CliRunner

# Match the existing adversarial HTTP fixture's exact import-only compatibility
# allowance. The locked HTTPX backend remains supported by this Starlette release.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message=re.escape(
            "Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead."
        ),
        category=StarletteDeprecationWarning,
    )
    from fastapi.testclient import TestClient

from hfcache.api.app import create_app
from hfcache.api.operations import OperationStore
from hfcache.cli import app
from hfcache.client import ApiClient
from hfcache.identity import new_run_id
from hfcache.logging import bind_run, reset
from hfcache.server_config import InstalledPolicy, validate_server_config_mapping
from hfcache.verification_executor import VerificationWorker, serve_worker, validate_listener
from hfcache.verification_protocol import VerificationClient


class ApiCli:
    def __init__(self, token, settings, application, web, exchange):
        self.token, self.settings, self.application, self.web = token, settings, application, web
        self.exchange = exchange
        self.patch: pytest.MonkeyPatch
        self.runner = CliRunner()

    def invoke(self, arguments, *, json_output=True):
        flags = [
            "--client-config",
            str(self.settings),
            "--api-url",
            "http://localhost",
            "--api-token-file",
            str(self.token),
        ]
        if json_output:
            flags.append("--json")
        result = self.runner.invoke(app, [*flags, *arguments])
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            raise result.exception
        return result


@contextmanager
def private_verifier(config):
    """Exercise framed authenticated IPC and the real guarded verification service."""
    with TemporaryDirectory(prefix="hfv-") as directory:
        root = Path(directory)
        root.chmod(0o700)
        path = root / "verify.sock"
        stop = threading.Event()
        policy = InstalledPolicy.open(config)
        with (
            OperationStore(root / "state") as store,
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
        ):
            worker = VerificationWorker(policy, store)
            listener.bind(str(path))
            path.chmod(0o600)
            listener.listen(8)
            validate_listener(listener, path)
            thread = threading.Thread(
                target=serve_worker,
                args=(listener, worker),
                kwargs={"expected_uid": os.geteuid(), "stop": stop, "timeout_seconds": 1},
            )
            thread.start()
            try:
                yield VerificationClient(
                    path,
                    timeout_seconds=1,
                    poll_seconds=0.01,
                    expected_archive_id=policy.archive_id,
                )
            finally:
                stop.set()
                thread.join(10)
                assert not thread.is_alive()


@contextmanager
def api_cli(
    config_path: Path,
    *,
    hub_token_file=None,
    reader=False,
    page_size=100,
    maintenance_enabled=False,
):
    """Provision only fixture state; the real CLI/client/app/services execute."""
    with TemporaryDirectory(prefix="api-cli-", dir=config_path.parent) as directory:
        root = Path(directory)
        writer, read_token = root / "writer.token", root / "reader.token"
        writer.write_text("fixture-writer-" + "W" * 40)
        read_token.write_text("fixture-reader-" + "R" * 40)
        writer.chmod(0o600)
        read_token.chmod(0o600)
        settings = root / "client.toml"
        settings.write_text("schema_version=1\n")
        config = validate_server_config_mapping(
            {
                "schema_version": 1,
                "archive_config": str(config_path),
                "state_directory": str(root / "state"),
                "maintenance_enabled": maintenance_enabled,
                "credentials": {
                    "writer": {"file": str(writer)},
                    "reader": {"file": str(read_token)},
                },
                "listener": {"unix_enabled": False, "tcp_enabled": True},
                "limits": {"max_page_size": page_size},
            }
        )
        try:
            with private_verifier(config) as verifier:
                application = create_app(
                    config,
                    instance_lock_path=root / "daemon.lock",
                    hub_token_file=hub_token_file,
                    verification_executor=verifier,
                )
                with (
                    TestClient(
                        application, base_url="http://localhost", client=("127.0.0.1", 19000)
                    ) as web,
                    pytest.MonkeyPatch.context() as patch,
                ):

                    def exchange(request: httpx.Request) -> httpx.Response:
                        # Starlette selects HTTPX2 when MCP installs it. Keep the
                        # base client's maintained HTTPX transport independent,
                        # rather than borrowing a nominally different private pool.
                        response = web.request(
                            request.method,
                            str(request.url),
                            headers=request.headers.raw,
                            content=request.read(),
                            follow_redirects=False,
                        )
                        return httpx.Response(
                            response.status_code,
                            headers=response.headers.raw,
                            content=response.content,
                        )

                    patch.setattr(
                        "hfcache.cli_client.ApiClient",
                        lambda settings: ApiClient(
                            settings, transport=httpx.MockTransport(exchange)
                        ),
                    )
                    # These processes are distinct in deployment. Keep daemon logging
                    # installed and give only the in-process CLI its invocation context.
                    patch.setattr(
                        "hfcache.cli.configure_logging", lambda **_: bind_run(new_run_id())
                    )
                    remote = ApiCli(
                        read_token if reader else writer,
                        settings,
                        application,
                        web,
                        exchange,
                    )
                    remote.patch = patch
                    yield remote
        finally:
            # The app has drained and joined before restoring test process state.
            reset()
