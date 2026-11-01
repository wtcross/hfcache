"""Tiny source-serialized fixtures for owned installed functional deployments.

This constructs disposable ordinary metadata; it never invokes archive init,
contacts a Hub, bypasses authentication or replaces a service/API response.
The installed application remains responsible for every read and validation.
"""

import hashlib
import json
import os
import stat
import struct
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from hfcache import __version__
from hfcache.catalog_capture import extract_publication
from hfcache.catalog_cards import capture_repository_card
from hfcache.catalog_extractors import SourceAccess
from hfcache.catalog_models import PublicationObservation, RepositoryTagSnapshot
from hfcache.config import load_config
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    RunId,
    new_run_id,
    new_transaction_id,
)
from hfcache.manifests import RevisionManifest
from hfcache.models import Reference
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    PUBLISHED_FILE_MODE,
    create_staging,
    published_repositories,
)
from hfcache.recovery import apply_recovery, plan_recovery
from hfcache.reporting import RunReport, VerificationReport
from hfcache.services.queries import LocalQueries
from hfcache.storage import SENTINEL_MODE
from hfcache.transactions import open_transaction
from tests.fixtures import examples
from tests.fixtures.gguf import gguf

MAXIMUM_ENTRIES = 4096
MAXIMUM_BYTES = 8 * 1024 * 1024
PUBLICATION_CONTENT = b"inert owned functional publication\n"
RICH_MODEL_CONTENT = gguf()[0]
HOSTILE_README = (
    b"---\nlanguage: en\nlicense: mit\n---\n# Owned inert card fixture\n"
    b"[relative guide](docs/guide.md) [external guide](https://example.invalid/guide)\n"
    b"![remote image must not load](https://example.invalid/tracker.svg)\n"
    b"```html\n<script>globalThis.fixtureExecuted = true</script>\n"
    b'<iframe src="https://example.invalid/frame"></iframe>\n'
    b'<form action="https://example.invalid/submit"><input name="value"></form>\n'
    b"```\n`javascript:alert(1)` is inert code, never a navigation target.\n"
)


# Explicit source-only opt-in corpus. The synthetic credential is never real.
BROWSER_SECRET = "hf_" + "A" * 32
BROWSER_READMES = {
    11: b"# Owned secret suppression fixture\n" + BROWSER_SECRET.encode() + b"\n",
    12: (
        b"# Owned raw active corpus\n<script src='https://example.inval"
        b"id/script.js'>globalThis.browserCorpusExecuted=true</script>"
        b"\n<iframe src='https://example.invalid/frame'></iframe>\n<form"
        b" action='https://example.invalid/post'><input autofocus onfo"
        b"cus='alert(1)'></form>\n<svg onload='alert(1)'><style>@font-f"
        b"ace{src:url(https://example.invalid/font.woff2)}</style></sv"
        b"g>\n<Component onClick={globalThis.browserCorpusExecuted=true"
        b"}/>\n[entity URL](java&#x73;cript:alert)\n"
    ),
    13: (
        b"---\nlanguage: en\nlicense: mit\n---\n# Owned unsafe URL corpus\n"
        b"[unsafe scheme](javascript:alert) [encoded scheme](java&#x73"
        b";cript:alert)\n"
    ),
    14: b"# Owned bounded Markdown corpus\n"
    + b"> " * 40
    + b"Owned nested boundary\n\n"
    + b"| column | value |\n|---|---|\n"
    + b"| cell | text |\n" * 64
    + b"\n```text\nOwned bounded code\n```\n"
    + b"x" * 8192
    + b"\n",
    15: (
        b"---\nlanguage: en\nlicense: mit\n---\n# Owned browser read corpu"
        b"s\n[relative guide](docs/guide.md) [external guide](https://e"
        b"xample.invalid/guide)\n![remote media](https://example.invali"
        b"d/tracker.svg)\n[font resource](https://example.invalid/font."
        b"woff2) [script resource](https://example.invalid/script.js)\n"
        b"## Repeated browser heading\nOne.\n## Repeated browser heading"
        b"\nTwo.\n| browser column | value |\n|---|---|\n| corpus row | bo"
        b"unded |\n\n```html\n<script>globalThis.browserCorpusExecuted=tr"
        b"ue</script>\n<iframe src='https://example.invalid/frame'></if"
        b"rame>\n```\n"
    ),
}
BROWSER_DATASET_README = (
    b"---\nconfigs:\n- config_name: browser-small\n  data_files: data"
    b".json\ndataset_info:\n- config_name: browser-small\n  features:"
    b"\n  - name: text\n    dtype: string\n  splits:\n  - name: train\n"
    b"    num_examples: 1\n---\n# Owned dataset declaration corpus\nD"
    b"eclared metadata is not a measured row count.\n"
)


def write_model(path, model):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.to_json(), encoding="utf-8")


def browser_model_files() -> dict[str, bytes]:
    """Tiny real parser inputs, shared with the owned native differential recipe."""

    def header(
        file_type: int,
        tensor_type: int,
        extra: dict[str, tuple[int, int | str]] | None = None,
    ) -> bytes:
        metadata: dict[str, tuple[int, int | str]] = {
            "general.file_type": (4, file_type),
            "general.architecture": (8, "llama"),
        }
        metadata.update(extra or {})
        return gguf(metadata, tensors=[("weight", (256,), tensor_type, 0)], body_bytes=1024)[0]

    tensor = json.dumps(
        {"weight": {"dtype": "I32", "shape": [4], "data_offsets": [0, 16]}},
        separators=(",", ":"),
    ).encode()
    return {
        "primary-q4.gguf": header(2, 2),
        "gptq/config.json": (
            b'{"model_type":"llama","quantization_config":'
            b'{"quant_method":"gptq","bits":8,"group_size":128}}\n'
        ),
        "gptq/model.safetensors": struct.pack("<Q", len(tensor)) + tensor + b"\xa5" * 16,
        "adapter-q8.gguf": header(7, 8, {"general.type": (8, "adapter")}),
        "mmproj-q4.gguf": header(3, 3, {"general.type": (8, "mmproj")}),
        "future-q5.gguf": header(8, 6, {"general.architecture": (8, "future-architecture")}),
        "split-q2-00001-of-00002.gguf": header(
            10, 10, {"split.no": (2, 0), "split.count": (2, 2), "split.tensors.count": (5, 2)}
        ),
    }


def seed_publication(  # noqa: PLR0913 - exact publication identity plus opt-in fixture contents
    queries,
    repository_type,
    repository_id,
    number,
    *,
    generation=1,
    readme=False,
    git_oids=False,
    readme_source=None,
    opaque=False,
    technical_variants=False,
):
    identity = RepositoryIdentity.of(repository_type, repository_id)
    repository = queries.layout.repository(identity)
    sha = CommitSha(f"{number:040x}")
    publication = PublicationId(f"{number:032x}")
    tree = repository.instance(sha, publication)
    tree.mkdir(parents=True)
    filename = "model-Q4_K_M.gguf" if repository_type == "model" else "data.json"
    files = {filename: RICH_MODEL_CONTENT if readme else PUBLICATION_CONTENT}
    if technical_variants:
        assert repository_type == "model"
        assert readme
        assert not opaque
        files = browser_model_files()
    if opaque:
        files = {"opaque.weights": b"owned unsupported ordinary bytes\n"}
    if readme:
        files["README.md"] = HOSTILE_README if readme_source is None else readme_source
    if repository_type == "dataset" and readme_source is not None:
        files[filename] = b'{"text":"owned browser dataset"}\n'
    base = examples.manifest().model_dump(mode="json")
    entries = []
    for path, content in sorted(files.items()):
        (tree / path).parent.mkdir(parents=True, exist_ok=True)
        (tree / path).write_bytes(content)
        entry = base["files"][0] | {
            "path": path,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        if git_oids:
            # Git object identity is protocol metadata, not a security digest.
            header = b"blob " + str(len(content)).encode("ascii") + b"\0"
            entry["upstream"] = entry["upstream"] | {
                "git_oid": hashlib.sha1(header + content, usedforsecurity=False).hexdigest()
            }
        entries.append(entry)
    total_bytes = sum(map(len, files.values()))
    manifest = RevisionManifest.model_validate(
        base
        | {
            "repository_type": repository_type,
            "repository_id": repository_id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": generation,
            "tree": str(repository.manifest_tree_field(sha, publication)),
            "files": entries,
            "dependencies": [],
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "verification": base["verification"]
            | {"reused_digests": 0, "hashed_objects": len(entries), "hashed_bytes": total_bytes},
        }
    )
    reference = Reference.model_validate(
        examples.reference().model_dump(mode="json")
        | {
            "repository_type": repository_type,
            "repository_id": repository_id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": generation,
            "tree": str(repository.tree_reference(sha, publication)),
            "manifest": str(repository.manifest_reference(sha, publication)),
        }
    )
    write_model(repository.manifest(sha, publication), manifest)
    write_model(repository.revision_ref(sha), reference)
    write_model(repository.current_ref, reference)
    return manifest


def seed_recovery_evidence(queries, model, *, archive_id, now):
    """Use TX-01/TX-04 builders; unknown siblings grant no cleanup authority."""
    envelope = {
        "application_version": __version__,
        "archive_id": archive_id,
        "config_fingerprint": queries.config.fingerprint(),
        "hostname": "owned-functional-fixture",
        "huggingface_hub_version": "1.24.0",
        "invocation_mode": "interactive",
        "python_version": "3.14.6",
    }

    def abandoned(number):
        identifier = new_transaction_id()
        transaction = open_transaction(
            queries.layout,
            transaction_id=identifier,
            operation="publication",
            run_id=new_run_id(),
            archive_id=archive_id,
            config_fingerprint=envelope["config_fingerprint"],
            repository_type=model.repository_type,
            repository_id=model.repository_id,
            commit_sha=f"{number:040x}",
            publication_id=f"{number:032x}",
        )
        staging = create_staging(queries.layout, identifier)
        payload = staging.tree / "model-Q4_K_M.gguf"
        payload.write_bytes(RICH_MODEL_CONTENT)
        payload.chmod(PUBLISHED_FILE_MODE)
        transaction.checkpoint(
            "staging_created", staging_path=str(queries.layout.archive_relative(staging.directory))
        )
        old = (now - timedelta(hours=48)).timestamp()
        os.utime(staging.directory, (old, old))
        return identifier

    completed = abandoned(41)
    plan = plan_recovery(queries.layout, stale_staging_age_hours=24, now=now)
    if plan.blocked or len(plan.actionable) != 1:
        msg = "fresh fixture did not produce exactly one recoverable publication"
        raise ValueError(msg)
    report, _ = apply_recovery(queries.layout, plan, envelope=envelope, started_at=now)
    pending = abandoned(42)
    unknown = []
    for directory in (queries.layout.staging, queries.layout.quarantine):
        path = directory / "unknown-owned-sibling" / "keep.txt"
        path.parent.mkdir(mode=0o700)
        path.write_bytes(b"unknown ordinary fixture evidence must remain\n")
        path.chmod(0o600)
        unknown.append(str(queries.layout.archive_relative(path)))
    return {
        "completed_quarantine_transaction_id": completed,
        "pending_recovery_transaction_id": pending,
        "recovery_report": str(queries.layout.archive_relative(report)),
        "unknown_files": unknown,
        "required_order": [
            "recover preview and original apply for pending_recovery_transaction_id",
            "offline catalog refresh with technical=true to capture the manifest-listed README",
            "explicit quarantine cleanup, prune round, and unmanaged-only purge",
        ],
        "repair": "pending: this fixture supplies no installed owned Hub adapter",
    }


def seed_browser_reads(queries, config, workspace) -> dict:
    """Source capture/extraction before pending journals; never an installed job."""
    rows = []
    for path in queries.layout.published.rglob("*"):
        path.chmod(PUBLISHED_DIRECTORY_MODE if path.is_dir() else PUBLISHED_FILE_MODE)
    identities = [("model", "fixture/model", range(11, 16)), ("dataset", "fixture/data", [21])]
    for kind, name, numbers in identities:
        identity = RepositoryIdentity.of(kind, name)
        repository = queries.layout.repository(identity)
        for number in numbers:
            sha, publication = CommitSha(f"{number:040x}"), PublicationId(f"{number:032x}")
            manifest_path = repository.manifest(sha, publication)
            manifest = RevisionManifest.model_validate_json(manifest_path.read_bytes())
            digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            extracted = extract_publication(SourceAccess(queries.layout, manifest))
            observation = PublicationObservation(
                archive_id=queries.config.storage.archive_id,
                repository_type=identity.type,
                repository_id=name,
                commit_sha=sha,
                publication_id=publication,
                publication_generation=manifest.publication_generation,
                manifest_path=str(queries.layout.archive_relative(manifest_path)),
                manifest_digest=digest,
                observed_at=datetime.now(UTC),
                status=extracted.status,
                sources=extracted.sources,
                variants=extracted.variants,
                dataset_formats=extracted.dataset_formats,
                diagnostics=extracted.diagnostics,
            )
            card = capture_repository_card(
                SourceAccess(queries.layout, manifest),
                digest,
                archive_id=queries.config.storage.archive_id,
            )
            write_model(repository.observation(sha, publication), observation)
            write_model(repository.card(sha, publication), card)
            rows.append(
                {
                    "repository_type": kind,
                    "repository_id": name,
                    "commit_sha": str(sha),
                    "publication_id": str(publication),
                    "publication_generation": manifest.publication_generation,
                    "manifest_sha256": digest,
                    "readme_sha256": card.expected_source_sha256,
                    "readme_bytes": next(f.size for f in manifest.files if f.path == "README.md"),
                    "card_state": card.state,
                    "card_diagnostics": list(card.diagnostics),
                    "presentation_sha256": card.presentation_sha256,
                    "technical_status": extracted.status,
                }
            )
    final = config.read_bytes()
    temporary = final + (
        b'\n[[repositories]]\ntype="dataset"\nid="fixture/unmanaged"\nenab'
        b'led=false\ntags=["browser-last-observed"]\n'
    )
    config.write_bytes(temporary)
    source = load_config(config)
    (workspace / "browser-curation-source.toml").write_bytes(temporary)
    tag = RepositoryTagSnapshot(
        archive_id=source.storage.archive_id,
        repository_type="dataset",
        repository_id="fixture/unmanaged",
        tags=next(
            row.tags
            for row in source.repositories
            if row.type == "dataset" and row.id == "fixture/unmanaged"
        ),
        observed_at=datetime.now(UTC),
        curation_fingerprint=source.curation_fingerprint(),
    )
    write_model(
        queries.layout.repository(
            RepositoryIdentity.of("dataset", "fixture/unmanaged")
        ).tag_snapshot,
        tag,
    )
    config.write_bytes(final)
    assert "fixture/unmanaged" not in {r.id for r in load_config(config).repositories}
    published = {identity.selector for identity in published_repositories(queries.layout)}
    configured = {row.type + ":" + row.id for row in load_config(config).repositories}
    return {
        "configured_repository_count": len(configured),
        "repository_union_count": len(configured | published),
        "provenance": (
            "core capture_repository_card/extract_publication and existin"
            "g typed models during fresh construction BEFORE pending jour"
            "nals; no installed job/NFS/Hub claim"
        ),
        "unpublished_selectors": [
            ("model" if n % 2 == 0 else "dataset") + f":browser/unpublished-{n:02d}"
            for n in range(26)
        ],
        "shared_unpublished_tag": "browser-page",
        "unpublished_unique_tag_prefix": "browser-",
        "unmanaged_last_observed_tag": "browser-last-observed",
        "curation_source_config": str(workspace / "browser-curation-source.toml"),
        "cards": rows,
        "raw_corpus_labels": {
            11: "Owned secret suppression fixture",
            12: "Owned raw active corpus",
            13: "Owned unsafe URL corpus",
            14: "Owned bounded Markdown corpus",
            15: "Owned browser read corpus",
            21: "Owned dataset declaration corpus",
        },
        "synthetic_secret_expression": "hf_ + A*32",
        "current_model_number": 15,
        "current_dataset_number": 21,
    }


def seed_archive(  # noqa: PLR0912, PLR0915 - preserve the existing opt-in constructor
    workspace: Path,
    *,
    fixture_root: Path | None = None,
    rich: bool = False,
    browser_reads: bool = False,
) -> dict:
    """Seed only a fresh private directory; rich opts into offline workflow evidence.

    Rich data supplies no captured card or installed job result. Its pending
    publication must be recovered before technical refresh/maintenance, using
    an independently owned real NFS mount and installed writer prerequisites.
    """
    if browser_reads and not rich:
        msg = "browser_reads requires explicit rich fresh construction"
        raise ValueError(msg)
    base = (
        fixture_root
        if fixture_root is not None
        else Path(__file__).absolute().parents[1] / ".scratch"
    )
    if (
        not workspace.is_absolute()
        or not workspace.is_relative_to(base)
        or workspace == base
        or workspace.resolve() != workspace
    ):
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
    archive_id = str(uuid4()) if rich else examples.ARCHIVE_ID
    config = workspace / "archive.toml"
    config.write_text(
        "schema_version=1\n[storage]\narchive_root="
        + json.dumps(str(archive))
        + "\narchive_id="
        + json.dumps(archive_id)
        + ("\nminimum_free_space_gib=0\nminimum_free_space_percent=0" if rich else "")
        + '\n[[repositories]]\ntype="model"\nid="fixture/model"\nenabled=false\n'
        + 'tags=["functional"]\n[[repositories]]\ntype="dataset"\nid="fixture/data"\n'
        + "enabled=false\n",
        encoding="utf-8",
    )
    config.chmod(0o600)
    if browser_reads:
        with config.open("a") as stream:
            for n in range(26):
                stream.write(
                    "\n[[repositories]]\ntype="
                    + json.dumps("model" if n % 2 == 0 else "dataset")
                    + "\nid="
                    + json.dumps(f"browser/unpublished-{n:02d}")
                    + "\nenabled=false\ntags="
                    + json.dumps(["browser-page", f"browser-{n:02d}"])
                    + "\n"
                )
    queries = LocalQueries(load_config(config))
    for directory in queries.layout.required_directories():
        directory.path.mkdir(parents=True, exist_ok=True)
    sentinel = examples.sentinel()
    if rich:
        sentinel = type(sentinel).model_validate(
            sentinel.model_dump(mode="json") | {"archive_id": archive_id}
        )
    write_model(queries.layout.sentinel, sentinel)
    model = seed_publication(
        queries,
        "model",
        "fixture/model",
        11,
        readme=rich,
        git_oids=rich,
        readme_source=BROWSER_READMES[11] if browser_reads else None,
    )
    if rich:
        for generation, number in enumerate(range(12, 16), start=2):
            model = seed_publication(
                queries,
                "model",
                "fixture/model",
                number,
                generation=generation,
                readme=True,
                git_oids=True,
                readme_source=BROWSER_READMES[number] if browser_reads else None,
                opaque=browser_reads and number in {12, 13},
                technical_variants=browser_reads and number == 15,
            )
        seed_publication(queries, "dataset", "fixture/unmanaged", 31, git_oids=True)
    seed_publication(
        queries,
        "dataset",
        "fixture/data",
        21,
        git_oids=rich,
        readme=browser_reads,
        readme_source=BROWSER_DATASET_README if browser_reads else None,
    )
    corpus = seed_browser_reads(queries, config, workspace) if browser_reads else None
    reports = (
        RunReport.model_validate(
            examples.run_report().model_dump(mode="json") | {"run_id": "1" * 32}
        ),
        VerificationReport.model_validate(
            examples.verification_report().model_dump(mode="json") | {"run_id": "2" * 32}
        ),
    )
    if rich:
        # These remain explicitly synthetic report fixtures, never evidence of
        # an installed job. Do not seed a fabricated current corruption finding.
        shared = {"archive_id": archive_id, "config_fingerprint": queries.config.fingerprint()}
        reports = (
            RunReport.model_validate(
                reports[0].model_dump(mode="json") | shared | {"repositories": [], "totals": {}}
            ),
            VerificationReport.model_validate(
                reports[1].model_dump(mode="json")
                | shared
                | {
                    "errors": [],
                    "exit_code": 0,
                    "findings": [],
                    "outcome": "success",
                    "verification_outcome": "clean",
                    "scope": {
                        "repositories": 0,
                        "revisions": 0,
                        "unique_bytes_read": 0,
                        "unique_objects_read": 0,
                    },
                    "throughput_bytes_per_second": 0.0,
                }
            ),
        )
    for report in reports:
        path = queries.layout.run_report(report.started_at, RunId(report.run_id))
        write_model(path, report)
        if rich:
            path.chmod(0o600)
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
    result: dict = {
        "schema_version": 1,
        "archive_config": str(config),
        "archive_root": str(archive),
        "archive_id": archive_id,
        "mcp_arguments": arguments,
        "scope": "synthetic ordinary metadata serialized by original models; no NFS/Hub claim",
    }
    if rich:
        result["rich"] = seed_recovery_evidence(
            queries, model, archive_id=archive_id, now=datetime.now(UTC)
        ) | {
            "model_repository": "model:fixture/model",
            "current_commit_sha": model.commit_sha,
            "current_publication_id": model.publication_id,
            "prune_candidate_commit_sha": f"{11:040x}",
            "purge_repository": "dataset:fixture/unmanaged",
            "readme_sha256": hashlib.sha256(HOSTILE_README).hexdigest(),
            "readme_bytes": len(HOSTILE_README),
            "card_state_before_installed_refresh": "not_captured",
            "synthetic_report_ids": [report.run_id for report in reports],
            "report_scope": "source-serialized examples, not evidence of installed jobs",
        }
        if corpus is not None:
            result["browser_reads"] = corpus
            current = next(
                row
                for row in corpus["cards"]
                if row["repository_type"] == "model" and row["publication_generation"] == 5
            )
            result["rich"].update(
                readme_sha256=current["readme_sha256"],
                readme_bytes=current["readme_bytes"],
                card_state_before_installed_refresh=current["card_state"],
            )
        # Only the newly constructed ordinary fixture is visited. Preserve the
        # original publication/private mode contract on a later owned copy.
        archive.chmod(0o750)
        queries.layout.sentinel.chmod(SENTINEL_MODE)
        for directory in queries.layout.required_directories():
            directory.path.chmod(directory.mode)
        for path in queries.layout.published.rglob("*"):
            path.chmod(PUBLISHED_DIRECTORY_MODE if path.is_dir() else PUBLISHED_FILE_MODE)
    return result


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
