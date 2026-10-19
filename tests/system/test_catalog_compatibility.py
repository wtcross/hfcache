"""V52-V54: actual installed pre-feature binaries preserve unknown catalog state."""

import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationStore
from hfcache.client_models import ClientOperation
from hfcache.paths import ArchiveLayout
from hfcache.server_config import InstalledPolicy
from hfcache.services.commands import CommandServices
from hfcache.services.context import ExecutionContext
from hfcache.services.requests import CatalogRefreshRequest
from tests.unit import test_catalog_lifecycle as lifecycle
from tests.unit import test_synchronize as sync_fixtures
from tests.unit.test_mcp_tools import snapshot

pytestmark = pytest.mark.build
ROOT = Path(__file__).resolve().parents[2]
_local_lock = lifecycle._local_lock
config = lifecycle.config
hub = lifecycle.hub
client = lifecycle.client
layout = lifecycle.layout
service = lifecycle.service
OLD_TOOLS = {
    "get_archive_status",
    "list_repositories",
    "list_revisions",
    "get_current_reference",
    "get_revision_manifest",
    "list_run_reports",
    "get_run_report",
    "get_verification_report",
    "estimate_verification",
}


def run(*args, cwd=None, check=True):
    completed = subprocess.run(
        args, cwd=cwd, check=False, capture_output=True, text=True, timeout=120
    )
    if check and completed.returncode:
        pytest.fail(completed.stderr[-8192:])
    return completed


@dataclass(frozen=True)
class OldRuntime:
    revision: str
    source: Path
    python: Path
    cli: Path
    wheel_sha256: str


@pytest.fixture(scope="module", params=["75d93a5", "4088994"])
def old_runtime(request, tmp_path_factory):
    workspace = tmp_path_factory.mktemp("old-catalog-" + request.param)
    source = workspace / "source"
    source.mkdir()
    archive = subprocess.run(
        ["git", "archive", "--format=tar", request.param],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(source, filter="data")
    uv = shutil.which("uv")
    assert uv is not None
    dist = workspace / "dist"
    run(uv, "build", "--offline", "--out-dir", str(dist), cwd=source)
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    requirements = workspace / "requirements.txt"
    run(
        uv,
        "export",
        "--locked",
        "--extra",
        "server",
        "--extra",
        "mcp",
        "--no-dev",
        "--no-emit-project",
        "--no-hashes",
        "--output-file",
        str(requirements),
        cwd=source,
    )
    environment = workspace / "environment"
    run(uv, "venv", "--offline", "--python", sys.executable, str(environment), cwd=workspace)
    python = environment / "bin/python"
    run(uv, "pip", "sync", "--offline", "--python", str(python), str(requirements), cwd=workspace)
    run(
        uv,
        "pip",
        "install",
        "--offline",
        "--no-deps",
        "--python",
        str(python),
        str(wheels[0]),
        cwd=workspace,
    )
    return OldRuntime(
        request.param,
        source,
        python,
        environment / "bin/hfcache",
        hashlib.sha256(wheels[0].read_bytes()).hexdigest(),
    )


def test_actual_old_binary_catalog_compatibility(  # noqa: PLR0915 - one exact target/layout/store drill
    old_runtime, service, layout, tmp_path
):
    assert service.synchronize().exit_code == 0
    policy = tmp_path / "target.toml"
    text = sync_fixtures.CONFIG.format(
        root=layout.root, archive_id=service.config.storage.archive_id, reserve_gib=0
    )
    text += '\n[hub]\ntoken_mode="disabled"\n'
    policy.write_text(text)
    cli_results = []
    for name, tags in (("old", None), ("empty", "[]"), ("tagged", '["coding"]')):
        candidate = tmp_path / (name + ".toml")
        candidate.write_text(
            text
            if tags is None
            else text.replace('type = "model"', 'type = "model"\ntags = ' + tags, 1)
        )
        completed = run(
            str(old_runtime.cli),
            "--config",
            str(candidate),
            "--json",
            "config",
            "validate",
            "--local",
            check=False,
            cwd=tmp_path,
        )
        cli_results.append(completed.returncode)
    assert cli_results == [0, 10, 10]
    installed = InstalledPolicy(policy, layout.root, service.config.storage.archive_id)
    state = tmp_path / "operation-state"
    context = ExecutionContext.create()
    with OperationStore(state) as store:
        principal = Principal(CredentialClass.REST_WRITER)
        done = store.admit(
            principal, "completed-refresh", "/api/v1/catalog/refreshes", {}, installed.snapshot
        ).receipt
        store.transition(done.operation_id, "running", domain_run_id=context.run_id)
        outcome = CommandServices(installed.snapshot().config, context).refresh_catalog(
            CatalogRefreshRequest(technical=False)
        )
        assert outcome.exit_code == 0
        envelope = outcome.envelope(context)
        terminal = store.transition(done.operation_id, "succeeded", envelope=envelope)
        queued = store.admit(
            principal, "queued-refresh", "/api/v1/catalog/refreshes", {}, installed.snapshot
        ).receipt
        public = {
            key: value
            for key, value in terminal.model_dump(mode="json").items()
            if key in ClientOperation.model_fields
        }
        public["result_recorded"] = True
    controls = {}
    for name in ("control", "extended"):
        root = tmp_path / name
        root.mkdir(mode=0o750)
        control = ArchiveLayout(root)
        for spec in control.required_directories():
            spec.path.mkdir(parents=True, exist_ok=True)
            spec.path.chmod(spec.mode)
        control.sentinel.write_bytes(layout.sentinel.read_bytes())
        if name == "extended":
            control.metadata.mkdir(mode=0o2750)
        controls[name] = str(root)
    inputs = controls | {
        "source": str(old_runtime.source),
        "goldens": str(ROOT / "tests/fixtures/schemas"),
        "config": str(policy),
        "archive": str(layout.root),
        "state": str(state),
        "terminal": terminal.operation_id,
        "queued": queued.operation_id,
        "public": public,
        "result": envelope.model_dump(mode="json"),
        "mountinfo": (
            f"457 47 0:68 / {layout.root} rw,relatime shared:488 - nfs4 nas:/x rw,vers=4.2\n"
        ),
        "report": str(tmp_path / "old-report.json"),
    }
    descriptor = tmp_path / "probe.json"
    descriptor.write_text(json.dumps(inputs))
    before = snapshot(layout.root)
    run(
        str(old_runtime.python),
        "-I",
        str(ROOT / "tests/fixtures/catalog_old_probe.py"),
        str(descriptor),
        cwd=tmp_path,
    )
    report = json.loads((tmp_path / "old-report.json").read_text())
    assert snapshot(layout.root) == before
    assert report["old_client_refuses_refresh_route"] is True
    assert report["old_store_reads_refresh_route"] == "/api/v1/catalog/refreshes"
    assert report["terminal_result_preserved"] is True
    assert report["queued_restart"] == "interrupted_without_replay"
    assert set(report["old_mcp_tools"]) == OLD_TOOLS
    assert len(report["old_goldens_unchanged_and_parsed"]) == 17
    assert report["control_layouts"][0]["state"] == "initialized"
    assert report["control_layouts"][1]["state"] == "unusable"
    assert report["control_layouts"][1]["unknown_entries"] == ["published/metadata"]
    assert report["inspection_state"] == "unusable"
    assert "published/metadata" in report["unknown_entries"]
    assert report["inventory"] == [sync_fixtures.MODEL.selector]
    print(  # noqa: T201 - actual installed-target evidence retained by the build gate
        json.dumps(
            {
                "revision": old_runtime.revision,
                "wheel_sha256": old_runtime.wheel_sha256,
                "config_cli_exit_codes": cli_results,
                "report": report,
            },
            sort_keys=True,
        )
    )
