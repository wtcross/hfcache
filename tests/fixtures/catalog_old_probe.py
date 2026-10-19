"""Owned subprocess probe executed only by an isolated pre-feature installed Python."""

import asyncio
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from pydantic import ValidationError

import hfcache
from hfcache.api.operations import OperationStore
from hfcache.api.runner import OperationRunner
from hfcache.archive import inspect_archive
from hfcache.client_models import ClientOperation
from hfcache.config import load_config
from hfcache.mcp import create_mcp_app
from hfcache.paths import ArchiveLayout
from hfcache.publication import published_repositories
from hfcache.server_config import InstalledPolicy
from hfcache.storage import parse_mount_table


def probe(data):
    installed = Path(hfcache.__file__).resolve().parent
    source = Path(data["source"]) / "src" / "hfcache"
    assert installed != source
    assert str(source) not in sys.path
    files = list(source.rglob("*.py"))
    for path in files:
        assert (installed / path.relative_to(source)).read_bytes() == path.read_bytes()
    spec = importlib.util.spec_from_file_location(
        "old_examples", Path(data["source"]) / "tests/fixtures/examples.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    goldens = []
    for name, factory in module.EXAMPLES.items():
        current = Path(data["goldens"]) / (name + ".json")
        previous = Path(data["source"]) / "tests/fixtures/schemas" / (name + ".json")
        assert current.read_bytes() == previous.read_bytes()
        type(factory()).model_validate_json(current.read_bytes())
        goldens.append(name)
    config = load_config(Path(data["config"]))
    layout = ArchiveLayout(Path(data["archive"]))
    inspection = inspect_archive(
        layout, archive_id=config.storage.archive_id, table=parse_mount_table(data["mountinfo"])
    )
    controls = []
    for name in ("control", "extended"):
        root = Path(data[name])
        inspected = inspect_archive(
            ArchiveLayout(root),
            archive_id=config.storage.archive_id,
            table=parse_mount_table(data["mountinfo"].replace(data["archive"], str(root))),
        )
        controls.append(
            {
                "state": inspected.state,
                "unknown_entries": list(inspected.unknown_entries),
                "codes": [problem.code for problem in inspected.problems],
            }
        )
    inventory = [identity.selector for identity in published_repositories(layout)]
    terminal_path = Path(data["state"]) / (data["terminal"] + ".result.json")
    original_result = terminal_path.read_bytes()
    public_refused = False
    try:
        ClientOperation.model_validate(data["public"])
    except ValidationError:
        public_refused = True
    with OperationStore(Path(data["state"])) as store:
        terminal_before = store.get(data["terminal"]).model_dump(mode="json")
        result = store.result(data["terminal"]).model_dump(mode="json")
        assert store.get(data["queued"]).state == "queued"
        with OperationRunner(
            store, InstalledPolicy(Path(data["config"]), layout.root, config.storage.archive_id)
        ):
            assert store.get(data["queued"]).state == "interrupted"
        assert store.get(data["terminal"]).model_dump(mode="json") == terminal_before
        assert store.result(data["terminal"]).model_dump(mode="json") == result
    assert terminal_path.read_bytes() == original_result
    app = create_mcp_app(lambda: None)
    tools = asyncio.run(app.state.fastmcp_server.list_tools())
    return {
        "installed_source_files_equal": len(files),
        "installed_config_sha256": hashlib.sha256(
            (installed / "config.py").read_bytes()
        ).hexdigest(),
        "old_goldens_unchanged_and_parsed": sorted(goldens),
        "control_layouts": controls,
        "inspection_state": inspection.state,
        "inspection_codes": [problem.code for problem in inspection.problems],
        "unknown_entries": list(inspection.unknown_entries),
        "inventory": inventory,
        "old_client_refuses_refresh_route": public_refused,
        "old_store_reads_refresh_route": terminal_before["route"],
        "terminal_result_preserved": result == data["result"],
        "queued_restart": "interrupted_without_replay",
        "old_mcp_tools": sorted(tool.name for tool in tools),
    }


if __name__ == "__main__":
    inputs = json.loads(Path(sys.argv[1]).read_text())
    Path(inputs["report"]).write_text(json.dumps(probe(inputs), sort_keys=True))
