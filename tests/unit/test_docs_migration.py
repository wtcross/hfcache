"""Preserved agent history stays separate from maintained human documentation."""

import hashlib
import json
from urllib.parse import urlsplit

from tests.docs_contract import CHECKER, ROOT


def test_agent_entrypoints_share_one_router():
    alias = ROOT / "CLAUDE.md"
    assert alias.is_symlink()
    assert alias.resolve() == ROOT / "AGENTS.md"


def test_agent_planning_records_and_history_are_preserved():
    agents = ROOT / "docs/agents"
    for name in (
        "plans",
        "history",
        "reviews",
        "adr",
        "progress.md",
        "migration-manifest.json",
        "documentation-inventory.json",
        "historical-contract-map.md",
        "code-removals.md",
    ):
        assert (agents / name).exists(), name
    assert (agents / "plans/current.md").is_file()
    assert (agents / "plans/tasks").is_dir()
    text = (agents / "invariants.md").read_text()
    assert "INV-011" in text
    assert "INV-011" not in (ROOT / "docs/invariants.md").read_text()


def test_preserved_snapshots_match_their_recorded_content_hashes():
    manifests = sorted((ROOT / "docs/agents/history").rglob("manifest.json"))
    assert manifests
    for manifest in manifests:
        for row in json.loads(manifest.read_text()):
            snapshot = ROOT / row["snapshot"]
            assert snapshot.is_file(), row["snapshot"]
            assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == row["snapshot_sha256"], (
                snapshot
            )


def test_reusable_agent_guidance_links_resolve():
    entries = CHECKER["repository_index"](ROOT)
    agents = ROOT / "docs/agents"
    historical = {"progress.md", "historical-contract-map.md", "code-removals.md"}
    docs = [
        ROOT / "AGENTS.md",
        agents / "plans/current.md",
        *sorted(path for path in agents.glob("*.md") if path.name not in historical),
    ]
    # Archived records retain original links and bytes; validate current guidance.
    # Agent-to-agent links are valid here; human-to-agent links remain forbidden.
    for document in docs:
        links, _ = CHECKER["markdown_references"](document.read_text())
        for link in links:
            target, fragment = CHECKER["local_target"](ROOT, document, link, entries)
            if target is None:
                assert urlsplit(link).scheme or urlsplit(link).netloc, (document, link, fragment)
            elif fragment and target.suffix == ".md":
                assert fragment in CHECKER["markdown_references"](target.read_text())[1], (
                    document,
                    link,
                )
