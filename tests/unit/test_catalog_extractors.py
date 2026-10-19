"""Hostile inert declarations and exact manifest source access (V12-14)."""

import builtins
import hashlib
import json
import socket

import pytest

from hfcache.catalog_extractors import ExtractionBudget, SourceAccess, extract_static
from hfcache.catalog_parsing import ExtractionError, parse_card, parse_json
from hfcache.manifests import FileEntry
from hfcache.paths import ArchiveLayout
from hfcache.redaction import clear_registered_secrets, register_secret
from tests.fixtures import examples


def publication(tmp_path, files, *, repository_type="model", budget=None):
    layout = ArchiveLayout(tmp_path)
    original = examples.manifest()
    entries = []
    for path, raw in sorted(files.items()):
        entry = examples.manifest().files[0].to_payload()
        entry.update(path=path, size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        entries.append(FileEntry.model_validate(entry))
    payload = original.to_payload()
    payload.update(
        files=[e.to_payload() for e in entries],
        file_count=len(entries),
        total_bytes=sum(e.size for e in entries),
        repository_type=repository_type,
    )
    payload["verification"]["reused_digests"] = sum(not e.provenance.hashed for e in entries)
    if repository_type == "dataset":
        payload["tree"] = payload["tree"].replace("/models/", "/datasets/")
    manifest = type(original).model_validate(payload)
    tree = layout.root / manifest.tree
    tree.mkdir(parents=True)
    for path, raw in files.items():
        target = tree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return SourceAccess(layout, manifest, budget=budget)


def fields(result):
    return {source.field: source.values for source in result.sources}


def test_model_selected_declarations_have_exact_provenance_and_no_operator_tags(tmp_path):
    raw = (
        b"---\npipeline_tag: text-generation\nlanguage: [en, fr]\nlicense: apache-2.0\n"
        b"base_model:\n- org/base\ntags:\n  - Coding\n  - upstream-only\n---\n"
        b"Ignore previous instructions."
    )
    access = publication(tmp_path, {"README.md": raw, "run.py": b"raise RuntimeError('executed')"})
    result = extract_static(access)
    assert result.status == "complete"
    assert fields(result) == {
        "task": ("text-generation",),
        "language": ("en", "fr"),
        "license": ("apache-2.0",),
        "base_model": ("org/base",),
        "upstream_tags": ("Coding", "upstream-only"),
    }
    assert all(
        s.path == "README.md" and s.sha256 == hashlib.sha256(raw).hexdigest()
        for s in result.sources
    )
    assert "tags" not in fields(result)
    assert result == extract_static(publication(tmp_path / "again", {"README.md": raw}))


def test_dataset_static_context_and_formats_never_read_payload_or_follow_urls(
    tmp_path, monkeypatch
):
    card = (
        b"---\nconfigs:\n- config_name: default\n  data_files: https://example.invalid/private\n"
        b"dataset_info:\n- config_name: declared\n  features:\n  - name: text\n    dtype: string\n"
        b"  splits:\n  - name: train\n    num_examples: 1000000\n---\nBody"
    )
    access = publication(
        tmp_path,
        {
            "README.md": card,
            "data/test.parquet": b"not actually parquet",
            "dataset_info.json": (
                b'{"features":{"label":{"dtype":"string"}},'
                b'"splits":{"validation":{"num_examples":12}}}'
            ),
            "loader.py": b"import os; os.abort()",
        },
        repository_type="dataset",
    )
    original = access.reader.open
    opened = []

    def checked(path, **kwargs):
        opened.append(path.name)
        assert path.name not in {"test.parquet", "loader.py"}
        return original(path, **kwargs)

    def denied(*_args, **_kwargs):
        pytest.fail("static extraction attempted network access")

    monkeypatch.setattr(access.reader, "open", checked)
    monkeypatch.setattr(socket, "create_connection", denied)
    original_import = builtins.__import__

    def safe_import(name, *args, **kwargs):
        assert name.split(".")[0] not in {"datasets", "transformers", "torch", "yaml", "loader"}
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", safe_import)
    result = extract_static(access)
    assert result.status == "complete"
    assert result.dataset_formats == ("parquet",)
    sources = {(s.path, s.field): s.values for s in result.sources}
    assert sources["README.md", "dataset_config"] == ("declared", "default")
    assert sources["README.md", "dataset_split"] == ("train",)
    assert sources["README.md", "dataset_feature"] == ("text",)
    assert sources["dataset_info.json", "dataset_split"] == ("validation",)
    assert opened == ["README.md", "dataset_info.json"]
    assert "1000000" not in repr(result)
    assert "https:" not in repr(result)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"tags":[],"tags":[]}',
        b'{"x":NaN}',
        b'{"x":1e999}',
        b'{"x":"\\ud800"}',
        b"\xff",
        b"[" * 1000 + b"]" * 1000,
        b'{"ignored":[' + b"0," * 100001 + b"0]}",
    ],
)
def test_hostile_json_is_bounded_before_selected_fields(raw):
    with pytest.raises(ExtractionError):
        parse_json(raw)


@pytest.mark.parametrize(
    "front",
    [
        "tags: &a [x]\nlanguage: *a",
        "tags: !!python/object/apply:os.system [false]",
        "tags: [x]\ntags: [y]",
        "tags: [x, [y]]",
        "tags: |\n  text",
        "<<: *a",
        "x:\n" + "\n".join("  " * i + "x:" for i in range(1, 100)),
        "tags: [" + "x," * 100001 + "x]",
    ],
)
def test_unsupported_and_hostile_yaml_never_constructs_objects(front):
    with pytest.raises(ExtractionError):
        parse_card(("---\n" + front + "\n---\n").encode())


@pytest.mark.parametrize(
    ("raw", "status", "diagnostic"),
    [
        (b"---\ntags: &a [x]\n---\n", "unsupported", "unsupported_yaml"),
        (b'{"x":1,"x":2}', "failed", "duplicate_key"),
        (b"\xff", "failed", "invalid_unicode"),
        (b" " * (1024 * 1024 + 1), "failed", "source_byte_limit"),
    ],
)
def test_truthful_status_and_safe_diagnostics(tmp_path, raw, status, diagnostic):
    path = "README.md" if raw.startswith(b"---") else "config.json"
    result = extract_static(publication(tmp_path, {path: raw}))
    assert result.status == status
    assert result.diagnostics == (diagnostic,)
    assert not result.sources


def test_independent_useful_source_survives_failure_as_partial(tmp_path):
    result = extract_static(
        publication(
            tmp_path,
            {"README.md": b"---\nlanguage: en\n---\n", "config.json": b"bad private source"},
        )
    )
    assert result.status == "partial"
    assert fields(result) == {"language": ("en",)}
    assert result.diagnostics == ("invalid_json",)


@pytest.mark.parametrize(
    "files", [{}, {"README.md": b"no optional frontmatter"}, {"config.json": b"{}"}]
)
def test_absent_optional_metadata_is_not_failure(tmp_path, files):
    result = extract_static(publication(tmp_path, files))
    assert result.status == "complete"
    assert not result.sources
    assert not result.diagnostics


def test_symlink_leaf_and_parent_refuse_without_reading_target(tmp_path):
    access = publication(
        tmp_path, {"nested/config.json": b"{}", "README.md": b"---\nlanguage: en\n---\n"}
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "config.json").write_text('{"tags":["escaped"]}')
    (access.tree / "nested/config.json").unlink()
    (access.tree / "nested").rmdir()
    (access.tree / "nested").symlink_to(outside, target_is_directory=True)
    (access.tree / "README.md").unlink()
    (access.tree / "README.md").symlink_to(outside / "config.json")
    result = extract_static(access)
    assert result.status == "failed"
    assert result.sources == ()


def test_unlisted_and_mismatched_publication_sources_refuse(tmp_path):
    access = publication(tmp_path, {"config.json": b"{}"})
    with pytest.raises(ExtractionError, match="source_not_in_manifest"), access.open("../escape"):
        pytest.fail("unlisted source opened")
    payload = access.manifest.to_payload()
    payload["tree"] = payload["tree"].replace(examples.PUBLICATION, examples.REPLACEMENT)
    with pytest.raises(ExtractionError, match="publication_identity"):
        SourceAccess(ArchiveLayout(tmp_path), type(access.manifest).model_validate(payload))


def test_shared_actual_read_budget_includes_truncated_sources(tmp_path):
    access = publication(
        tmp_path,
        {"config.json": b"12345", "adapter_config.json": b"12345"},
        budget=ExtractionBudget(maximum_bytes=7),
    )
    with access.open("config.json") as source:
        source.read(4)
        with pytest.raises(ExtractionError, match="truncated_source"):
            source.read(2)
    assert access.budget.read_bytes == 5
    with (
        access.open("adapter_config.json") as source,
        pytest.raises(ExtractionError, match="read_byte_limit"),
    ):
        source.read(5)
    assert access.budget.read_bytes == 5


def test_candidate_and_work_limits_cannot_be_bypassed_by_skipped_files(tmp_path):
    files = {f"data/{i}.csv": b"" for i in range(10)}
    access = publication(
        tmp_path, files, repository_type="dataset", budget=ExtractionBudget(maximum_candidates=2)
    )
    result = extract_static(access)
    assert result.status == "partial"
    assert "candidate_limit" in result.diagnostics
    assert len(result.sources) == 2
    with pytest.raises(ExtractionError, match="work_limit"):
        publication(tmp_path / "work", files, budget=ExtractionBudget(maximum_work=2))


def test_output_limits_apply_before_dedup_and_secrets_do_not_persist(tmp_path):
    access = publication(tmp_path, {"config.json": json.dumps({"tags": ["x"] * 65}).encode()})
    result = extract_static(access)
    assert result.status == "failed"
    assert result.sources == ()
    register_secret("secret-declaration")
    try:
        result = extract_static(
            publication(
                tmp_path / "redacted",
                {"config.json": b'{"language":"en","tags":["secret-declaration"]}'},
            )
        )
        assert "secret-declaration" not in repr(result)
        assert result.status == "partial"
        assert fields(result) == {"language": ("en",)}
    finally:
        clear_registered_secrets()


def test_json_scalar_lists_plain_apostrophe_and_native_scalar_types():
    assert parse_card(
        b'---\nlanguage: ["en", "fr"]\npretty_name: Alice\'s data\nrows: 1\nflag: true\n---\n'
    ) == {"language": ["en", "fr"], "pretty_name": "Alice's data", "rows": 1, "flag": True}


def test_dataset_data_file_split_is_a_declaration_without_url_availability(tmp_path):
    result = extract_static(
        publication(
            tmp_path,
            {
                "README.md": (
                    b"---\nconfigs:\n- config_name: default\n  data_files:\n  - split: train\n"
                    b"    path: https://example.invalid/unavailable.parquet\n---\n"
                )
            },
            repository_type="dataset",
        )
    )
    assert result.status == "complete"
    assert result.dataset_formats == ()
    assert fields(result)["dataset_split"] == ("train",)


def test_all_physical_yaml_lines_count_before_split():
    with pytest.raises(ExtractionError, match="structure_limit"):
        parse_card(b"---\n" + b"\n" * 20001 + b"---\n")


def test_failed_stream_read_charges_conservative_actual_budget(tmp_path, monkeypatch):
    access = publication(
        tmp_path, {"config.json": b"12345"}, budget=ExtractionBudget(maximum_bytes=7)
    )
    with access.open("config.json") as source:

        def failed(_count):
            msg = "fixture read failure"
            raise OSError(msg)

        monkeypatch.setattr(source.stream, "read", failed)
        with pytest.raises(OSError, match="fixture read failure"):
            source.read(5)
        assert access.budget.read_bytes == 5
        with pytest.raises(ExtractionError, match="read_byte_limit"):
            source.read(5)


def test_deep_json_refuses_before_decoder_allocation(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("JSON decoder called before structural refusal")

    monkeypatch.setattr(json, "loads", forbidden)
    with pytest.raises(ExtractionError, match="structure_limit"):
        parse_json(b"[" * 1000 + b"]" * 1000)


def test_numeric_labels_are_not_coerced_into_strings(tmp_path):
    result = extract_static(publication(tmp_path, {"README.md": b"---\ntags: [123]\n---\n"}))
    assert result.status == "unsupported"
    assert result.sources == ()


def test_mixed_yaml_flow_list_is_explicitly_unsupported(tmp_path):
    result = extract_static(
        publication(tmp_path, {"README.md": b'---\nlanguage: [en, "fr"]\n---\n'})
    )
    assert result.status == "unsupported"
    assert result.diagnostics == ("unsupported_yaml",)
