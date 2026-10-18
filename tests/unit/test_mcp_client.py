"""MCP-004 example executes modern/legacy reads over actual disposable sockets."""

import asyncio
import importlib.util
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from hfcache.api.app import create_app
from hfcache.server import build_server
from hfcache.server_config import validate_server_config_mapping
from tests.unit.test_mcp_client_security import FakeClient, Reply, publication_frames
from tests.unit.test_mcp_tools import archive as archive_base  # noqa: F401 - fixture
from tests.unit.test_mcp_tools import (
    snapshot,
    socket_policy,  # noqa: F401 - fixture dependency
)
from tests.unit.test_server_bootstrap import (
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)


def load_example():
    name = "hfcache_mcp_client_example"
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[2] / "examples" / "mcp-client.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def example():
    return load_example()


@pytest.fixture
def archive(request):
    return request.getfixturevalue("archive_base")


@pytest.mark.parametrize("mode", ["auto", "legacy"])
@pytest.mark.parametrize("tls", [False, True])
def test_example_walks_actual_mounted_pages_and_one_exact_publication(
    archive, example, tmp_path, mode, tls
):
    server_config = archive.server
    certificate = None
    if tls:
        certificate = tmp_path / "certificate.pem"
        key = tmp_path / "private-key.pem"
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=localhost",
                "-addext",
                "subjectAltName=IP:127.0.0.1,DNS:localhost",
                "-keyout",
                str(key),
                "-out",
                str(certificate),
            ],
            check=True,
            capture_output=True,
        )
        server_config = validate_server_config_mapping(
            server_config.model_dump(mode="json")
            | {
                "listener": server_config.listener.model_dump(mode="json")
                | {
                    "tls": {"certificate": str(certificate), "private_key": str(key)},
                }
            }
        )
    app = create_app(server_config, instance_lock_path=tmp_path / "example.lock")
    server = build_server(app, server_config)
    seen = []
    with socket.socket() as channel:
        channel.bind(("127.0.0.1", 0))
        port = channel.getsockname()[1]
        settings = example.Settings(
            endpoint=f"{'https' if tls else 'http'}://127.0.0.1:{port}/mcp/",
            token_file=tmp_path / "mcp.token",
            ca_file=certificate,
            page_size=1,
            max_pages=20,
            timeout_seconds=10.0,
            mode=mode,
            repository_type="model",
            repository_id="alpha/model",
        )

        async def request():
            before = snapshot(archive.queries.layout.root, server_config.state_directory)
            result = await example.run(
                settings, on_page=lambda name, frame: seen.append((name, frame))
            )
            assert result == {
                "repository_count": 4,
                "manifest_files": 3,
                "manifest_dependencies": 2,
                "metadata_pages": 10,
            }
            assert snapshot(archive.queries.layout.root, server_config.state_directory) == before
            assert app.state.operations.list() == ()
            if mode == "auto" and not tls:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    str(Path(__file__).parents[2] / "examples" / "mcp-client.py"),
                    "--url",
                    settings.endpoint,
                    "--token-file",
                    str(settings.token_file),
                    "--page-size",
                    "1",
                    "--type",
                    "model",
                    "--repository",
                    "alpha/model",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                assert process.returncode == 0, stderr.decode()
                assert json.loads(stdout) == {"kind": "discovery_summary", **result}
                guide = (Path(__file__).parents[2] / "docs/mcp.md").read_text()
                documented = guide.split("```json\n", 1)[1].split("\n```", 1)[0]
                assert json.loads(stdout) == json.loads(documented)
                assert stderr == b""
                assert settings.token_file.read_bytes() not in stdout + stderr
                assert (
                    snapshot(archive.queries.layout.root, server_config.state_directory) == before
                )

        asyncio.run(exercise(server, [channel], request))
    reference = [frame for name, frame in seen if name == "get_current_reference"]
    assert len(reference) == 1
    exact = reference[0].envelope.data["reference"]
    assert exact["publication_id"] == archive.manifests[1].publication_id
    manifest_pages = [frame for name, frame in seen if name == "get_revision_manifest"]
    assert len(manifest_pages) == 5
    assert {frame.envelope.data["manifest"]["publication_id"] for frame in manifest_pages} == {
        exact["publication_id"]
    }
    assert all(frame.envelope.data["projection"] for frame in manifest_pages)
    assert all(frame.envelope.data["tree_base"] == "archive-root/" for frame in manifest_pages)
    assert len({frame.request_id for _, frame in seen}) == 10
    assert len({frame.config_fingerprint for _, frame in seen}) == 1
    assert len({frame.archive_id for _, frame in seen}) == 1
    assert app.state.credentials is None


def test_example_help_and_parse_errors_never_echo_rejected_arguments(example, capsys):
    with pytest.raises(SystemExit) as help_exit:
        example.main(["--help"])
    assert help_exit.value.code == 0
    assert "--token-file" in capsys.readouterr().out
    marker = "unregistered-private-cli-input"
    assert example.main(["--wrong", marker]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == example.FAILURE
    assert marker not in captured.err


def test_example_counts_valid_sorted_duplicate_dependency_keys(example, tmp_path):
    replies = publication_frames()
    entries = replies[-1]["envelope"]["data"]["entries"]
    entries.insert(0, dict(entries[0]))
    replies[-1]["envelope"]["data"]["total_entries"] = len(entries)
    client = FakeClient([Reply(item) for item in replies])
    token_file = tmp_path / "example.token"
    token_file.write_text("mcp-example-" + "D" * 48)
    token_file.chmod(0o600)
    reference = replies[1]["envelope"]["data"]["reference"]
    settings = example.Settings(
        endpoint="https://archive.example/mcp/",
        token_file=token_file,
        repository_type=reference["repository_type"],
        repository_id=reference["repository_id"],
    )
    result = asyncio.run(example.run(settings, client_factory=lambda *_: client))
    assert result["manifest_dependencies"] == len(entries)
    assert client.closed
