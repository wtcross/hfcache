"""Record relocation preserves provenance and a single execution authority."""

import hashlib
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/agents/migration-manifest.json"


@lru_cache
def original_paths(commit):
    return subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()


def original_path(row, field, commit):
    """Resolve an intentionally omitted historical spelling without losing provenance."""
    if field in row:
        assert field + "_path_sha256" not in row
        return row[field]
    digest = row[field + "_path_sha256"]
    matches = [
        name
        for name in original_paths(commit)
        if hashlib.sha256(name.encode()).hexdigest() == digest
    ]
    assert len(matches) == 1, (commit, digest)
    return matches[0]


def test_every_migrated_record_has_original_git_hash_and_unique_destination():
    manifest = json.loads(MANIFEST.read_text())
    records = manifest["records"]
    assert len({original_path(row, "old", manifest["baseline"]) for row in records}) == len(records)
    current = [row["new"] for row in records if not row.get("retired")]
    assert len(set(current)) == len(current)
    for row in records:
        old = original_path(row, "old", manifest["baseline"])
        original = subprocess.run(
            ["git", "show", f"{manifest['baseline']}:{old}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert hashlib.sha256(original).hexdigest() == row["sha256"]
        if row.get("retired"):
            assert row["retired"] is True
            assert row["retirement_reason"].strip()
            assert "new" not in row
        else:
            assert (ROOT / row["new"]).is_file(), row
        assert not (ROOT / old).exists(), row


def test_agent_entrypoint_and_single_selector_survive_relocation():
    assert (ROOT / "CLAUDE.md").is_symlink()
    assert (ROOT / "CLAUDE.md").resolve() == ROOT / "AGENTS.md"
    assert not (ROOT / "docs/plans").exists()
    selectors = list((ROOT / "docs").rglob("current.md"))
    assert selectors == [ROOT / "docs/agents/plans/current.md"]
    assert "docs/agents/plans/current.md" in (ROOT / "AGENTS.md").read_text()


def test_every_migration_markdown_link_has_an_existing_destination():
    documents = [
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        *(ROOT / "docs").rglob("*.md"),
    ]
    for document in documents:
        for target in re.findall(r"\]\(([^\s)]+)\)", document.read_text()):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("/"):
                continue
            relative = unquote(target.partition("#")[0])
            assert (document.parent / relative).exists(), (document, target)


def test_planning_invariant_and_process_decisions_have_agent_homes():
    assert "**`INV-011`" not in (ROOT / "docs/invariants.md").read_text()
    assert "**`INV-011`" in (ROOT / "docs/agents/invariants.md").read_text()
    for number in (80, 81, 82, 106, 107):
        assert (ROOT / f"docs/agents/adr/decision-{number:03}.md").exists()
        assert not (ROOT / f"docs/adr/decision-{number:03}.md").exists()


def test_original_documentation_inventory_accounts_for_each_tracked_document():
    manifest = json.loads(MANIFEST.read_text())
    inventory = json.loads((ROOT / "docs/agents/documentation-inventory.json").read_text())
    paths = original_paths(manifest["baseline"])
    expected = {p for p in paths if p.endswith(".md") and p != "CLAUDE.md"}
    retained = {
        original_path(row, "original", manifest["baseline"]) for row in inventory["documents"]
    }
    retired_rows = inventory["retired_documents"]
    retired = {original_path(row, "original", manifest["baseline"]) for row in retired_rows}
    assert not retained & retired
    assert retained | retired == expected
    assert len(retained) == len(inventory["documents"])
    assert len(retired) == len(retired_rows)
    assert all(row["reason"].strip() for row in retired_rows)
    assert all((ROOT / row["current"]).exists() for row in inventory["documents"])


def test_every_preserved_reference_snapshot_has_an_original_git_hash_and_current_home():
    manifests = sorted((ROOT / "docs/agents/history").rglob("manifest.json"))
    assert manifests
    snapshots = set()
    for manifest in manifests:
        for row in json.loads(manifest.read_text()):
            source = original_path(row, "source", row["git"])
            original = subprocess.run(
                ["git", "show", f"{row['git']}:{source}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            assert hashlib.sha256(original).hexdigest() == row["sha256"]
            assert row["snapshot"] not in snapshots
            snapshots.add(row["snapshot"])
            assert (ROOT / row["snapshot"]).is_file()
            assert (
                hashlib.sha256((ROOT / row["snapshot"]).read_bytes()).hexdigest()
                == row["snapshot_sha256"]
            )
            assert (ROOT / row.get("current_source", source)).is_file()
