"""Tiny source-serialized fixtures for owned installed functional deployments.

This constructs disposable ordinary metadata; it never invokes archive init,
contacts a Hub, bypasses authentication or replaces a service/API response.
The installed application remains responsible for every read and validation.
"""

import hashlib
import json
import os
import stat
from pathlib import Path

from hfcache.config import load_config
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, RunId
from hfcache.manifests import RevisionManifest
from hfcache.models import Reference
from hfcache.reporting import RunReport, VerificationReport
from hfcache.services.queries import LocalQueries
from tests.fixtures import examples

MAXIMUM_ENTRIES = 4096
MAXIMUM_BYTES = 8 * 1024 * 1024


def write_model(path, model):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.to_json(), encoding="utf-8")


def seed_publication(queries, repository_type, repository_id, number):
    identity = RepositoryIdentity.of(repository_type, repository_id)
    repository = queries.layout.repository(identity)
    sha = CommitSha(f"{number:040x}")
    publication = PublicationId(f"{number:032x}")
    tree = repository.instance(sha, publication)
    tree.mkdir(parents=True)
    content = b"inert owned functional publication\n"
    filename = "model-Q4_K_M.gguf" if repository_type == "model" else "data.json"
    (tree / filename).write_bytes(content)
    base = examples.manifest().model_dump(mode="json")
    entry = base["files"][0] | {
        "path": filename,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    manifest = RevisionManifest.model_validate(
        base
        | {
            "repository_type": repository_type,
            "repository_id": repository_id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": 1,
            "tree": str(repository.manifest_tree_field(sha, publication)),
            "files": [entry],
            "dependencies": [],
            "file_count": 1,
            "total_bytes": len(content),
            "verification": base["verification"]
            | {"reused_digests": 0, "hashed_objects": 1, "hashed_bytes": len(content)},
        }
    )
    reference = Reference.model_validate(
        examples.reference().model_dump(mode="json")
        | {
            "repository_type": repository_type,
            "repository_id": repository_id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": 1,
            "tree": str(repository.tree_reference(sha, publication)),
            "manifest": str(repository.manifest_reference(sha, publication)),
        }
    )
    write_model(repository.manifest(sha, publication), manifest)
    write_model(repository.revision_ref(sha), reference)
    write_model(repository.current_ref, reference)
    return manifest


def seed_archive(workspace: Path, *, fixture_root: Path | None = None) -> dict:
    """The caller supplies a fresh private positively owned fixture directory."""
    base = (
        fixture_root
        if fixture_root is not None
        else Path(__file__).absolute().parents[1] / ".scratch"
    )
    if not workspace.is_absolute() or not workspace.is_relative_to(base) or workspace == base:
        msg = "seed workspace must be a descendant of the explicitly owned fixture root"
        raise ValueError(msg)
    facts = workspace.lstat()
    if (
        not stat.S_ISDIR(facts.st_mode)
        or facts.st_uid != os.getuid()
        or facts.st_mode & 0o077
        or workspace.is_symlink()
        or any(workspace.iterdir())
    ):
        msg = "seed workspace must be fresh, private and current-user owned"
        raise ValueError(msg)
    archive = workspace / "archive"
    config = workspace / "archive.toml"
    config.write_text(
        "schema_version=1\n[storage]\narchive_root="
        + json.dumps(str(archive))
        + "\narchive_id="
        + json.dumps(examples.ARCHIVE_ID)
        + '\n[[repositories]]\ntype="model"\nid="fixture/model"\nenabled=false\n'
        + 'tags=["functional"]\n[[repositories]]\ntype="dataset"\nid="fixture/data"\n'
        + "enabled=false\n",
        encoding="utf-8",
    )
    config.chmod(0o600)
    queries = LocalQueries(load_config(config))
    for directory in queries.layout.required_directories():
        directory.path.mkdir(parents=True, exist_ok=True)
    write_model(queries.layout.sentinel, examples.sentinel())
    model = seed_publication(queries, "model", "fixture/model", 11)
    seed_publication(queries, "dataset", "fixture/data", 21)
    reports = (
        RunReport.model_validate(
            examples.run_report().model_dump(mode="json") | {"run_id": "1" * 32}
        ),
        VerificationReport.model_validate(
            examples.verification_report().model_dump(mode="json") | {"run_id": "2" * 32}
        ),
    )
    for report in reports:
        write_model(queries.layout.run_report(report.started_at, RunId(report.run_id)), report)
    arguments = {
        "get_archive_status": {},
        "list_repositories": {},
        "list_revisions": {},
        "get_current_reference": {"repository_type": "model", "repository_id": "fixture/model"},
        "get_revision_manifest": {
            "repository_type": "model",
            "repository_id": "fixture/model",
            "commit_sha": model.commit_sha,
            "publication_id": model.publication_id,
        },
        "list_run_reports": {},
        "get_run_report": {"run_id": reports[0].run_id},
        "get_verification_report": {"run_id": reports[1].run_id},
        "estimate_verification": {},
        "search_models": {},
        "search_datasets": {},
        "get_catalog_entry": {"repository_type": "model", "repository_id": "fixture/model"},
        "list_model_variants": {"repository_id": "fixture/model"},
        "get_catalog_facets": {"facet": "tag"},
    }
    return {
        "schema_version": 1,
        "archive_config": str(config),
        "archive_root": str(archive),
        "archive_id": examples.ARCHIVE_ID,
        "mcp_arguments": arguments,
        "scope": "synthetic ordinary metadata serialized by original models; no NFS/Hub claim",
    }


def snapshot(root: Path, *, fixture_root: Path | None = None) -> dict:
    """Capture only an already-owned tiny fixture, excluding read-induced atime."""
    base = (
        fixture_root
        if fixture_root is not None
        else Path(__file__).absolute().parents[1] / ".scratch"
    )
    if not root.is_absolute() or not root.is_relative_to(base) or root == base:
        msg = "snapshot root must be a descendant of the explicitly owned fixture root"
        raise ValueError(msg)
    result = {}
    pending = [root]
    discovered = 1
    while pending:
        path = pending.pop()
        if len(result) >= MAXIMUM_ENTRIES:
            msg = "owned fixture snapshot exceeded its entry bound"
            raise ValueError(msg)
        facts = path.lstat()
        if not stat.S_ISDIR(facts.st_mode) and not stat.S_ISREG(facts.st_mode):
            msg = "owned fixture snapshot contains an unsupported entry"
            raise ValueError(msg)
        if facts.st_size > MAXIMUM_BYTES:
            msg = "owned fixture snapshot exceeded its byte bound"
            raise ValueError(msg)
        result[str(path.relative_to(root))] = {
            "device": facts.st_dev,
            "inode": facts.st_ino,
            "mode": facts.st_mode,
            "uid": facts.st_uid,
            "gid": facts.st_gid,
            "links": facts.st_nlink,
            "size": facts.st_size,
            "mtime_ns": facts.st_mtime_ns,
            "ctime_ns": facts.st_ctime_ns,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
        }
        if stat.S_ISDIR(facts.st_mode):
            children = []
            with os.scandir(path) as entries:
                for entry in entries:
                    discovered += 1
                    if discovered > MAXIMUM_ENTRIES:
                        msg = "owned fixture snapshot exceeded its entry bound"
                        raise ValueError(msg)
                    children.append(Path(entry.path))
            pending.extend(sorted(children, reverse=True))
    return result
